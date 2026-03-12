from __future__ import annotations

import asyncio

from playwright.async_api import Browser, Page, Playwright, async_playwright

from ib_client.client import IBClient
from ib_client.exceptions import AuthenticationError
from ib_client.gateway import GatewayManager
from ib_client.logger import get_logger
from ib_client.models.session import LoginResult
from ib_client.settings import Settings


class AuthWorkflow:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = get_logger("ib_client.auth")
        self.gateway = GatewayManager(settings)

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

                async with IBClient(self.settings) as client:
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
