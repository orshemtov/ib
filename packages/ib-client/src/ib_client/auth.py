from __future__ import annotations

import asyncio

from playwright.async_api import Browser, Page, Playwright, async_playwright

from ib_client.client import IBClient
from ib_client.exceptions import AuthenticationError
from ib_client.gateway import GatewayManager
from ib_client.logger import get_logger
from ib_client.models.session import LoginResult
from ib_client.settings import (
    Settings,
    build_settings,
    client_kwargs_from_settings,
    gateway_kwargs_from_settings,
)


class AuthWorkflow:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        username: str | None = None,
        password: str | None = None,
        account_id: str | None = None,
        gateway_dir: str | None = "gateway",
        gateway_config_path: str | None = None,
        api_host: str = "localhost",
        api_port: int = 5001,
        use_ssl: bool = True,
        verify_ssl: bool = False,
        request_timeout_seconds: float = 30.0,
        tickle_interval_seconds: float = 60.0,
        playwright_headless: bool = False,
        playwright_timeout_seconds: float = 180.0,
    ) -> None:
        self.settings = settings or build_settings(
            username=username,
            password=password,
            account_id=account_id,
            gateway_dir=gateway_dir,
            gateway_config_path=gateway_config_path,
            api_host=api_host,
            api_port=api_port,
            use_ssl=use_ssl,
            verify_ssl=verify_ssl,
            request_timeout_seconds=request_timeout_seconds,
            tickle_interval_seconds=tickle_interval_seconds,
            playwright_headless=playwright_headless,
            playwright_timeout_seconds=playwright_timeout_seconds,
        )
        self.logger = get_logger("ib_client.auth")
        self.gateway = GatewayManager(**gateway_kwargs_from_settings(self.settings))

    async def login(self) -> LoginResult:
        gateway_started = False
        if not self.gateway.is_reachable() and self.settings.gateway_dir is not None:
            self.gateway.start()
            gateway_started = True
            await asyncio.sleep(5)

        browser_opened = False
        async with async_playwright() as playwright:
            browser, page = await self._open_browser(playwright)
            try:
                await self._fill_credentials(page)
                browser_opened = True

                async with IBClient(**client_kwargs_from_settings(self.settings)) as client:
                    status = await client.wait_for_authentication(
                        self.settings.playwright_timeout_seconds
                    )
                    if not status.authenticated:
                        raise AuthenticationError("Authentication did not complete before timeout")
            finally:
                await browser.close()

        return LoginResult(
            gateway_started=gateway_started,
            browser_opened=browser_opened,
            authenticated=True,
            message=(
                "Authentication complete. If 2FA was required, "
                "it has been completed in the browser."
            ),
        )

    async def _open_browser(self, playwright: Playwright) -> tuple[Browser, Page]:
        self.logger.info("opening_login_browser", origin=self.settings.gateway_origin)
        browser = await playwright.chromium.launch(headless=self.settings.playwright_headless)
        page = await browser.new_page(ignore_https_errors=not self.settings.verify_ssl)
        await page.goto(self.settings.gateway_origin, wait_until="domcontentloaded")
        return browser, page

    async def _fill_credentials(self, page: Page) -> None:
        if self.settings.username:
            username_input = page.locator('input[type="text"], input[name="username"]').first
            await username_input.fill(self.settings.username)
        if self.settings.password:
            await page.locator('input[type="password"]').first.fill(self.settings.password)

        submit_selector = (
            'button[type="submit"], input[type="submit"], '
            'button:has-text("Log In"), button:has-text("Login")'
        )
        submit = page.locator(submit_selector).first
        if await submit.count() > 0:
            await submit.click()

        self.logger.info(
            "awaiting_manual_2fa",
            timeout_seconds=self.settings.playwright_timeout_seconds,
            message="Complete any IBKR 2FA challenge in the browser window.",
        )
