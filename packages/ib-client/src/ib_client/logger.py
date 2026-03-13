from __future__ import annotations

import logging
import os
from collections.abc import MutableMapping
from typing import Any

import structlog


def _as_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def should_use_colors(mode: str, ci: bool) -> bool:
    if mode == "true":
        return True
    if mode == "false":
        return False
    return not ci


def _drop_color_message_key(
    _: Any, __: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    event_dict.setdefault("message", event_dict.get("event"))
    return event_dict


def configure_logging(
    *,
    log_level: str = "INFO",
    log_format: str = "plain",
    log_color: str = "auto",
) -> None:
    ci = _as_bool(os.getenv("CI"))
    use_colors = should_use_colors(log_color, ci)
    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        _drop_color_message_key,
    ]
    renderer: Any
    if log_format == "json":
        processors.insert(2, structlog.processors.TimeStamper(fmt="iso", utc=False))
        renderer = structlog.processors.JSONRenderer()
    else:
        processors.insert(2, structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False))
        renderer = structlog.dev.ConsoleRenderer(
            colors=use_colors,
            level_styles=structlog.dev.ConsoleRenderer.get_default_level_styles(colors=use_colors),
            pad_level=False,
            pad_event=0,
        )

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(message)s",
    )
    structlog.configure(
        processors=[
            *processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
        wrapper_class=structlog.stdlib.BoundLogger,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=processors,
        processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta, renderer],
    )
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
