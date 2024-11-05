import asyncio
from typing import Any
from playwright.async_api import BrowserContext, Locator, Error
from src.forgery.automation import execute_chromium


@execute_chromium(
    profiles="profiles.json",
    config="scripts/telegram/updater/config.json"
)
async def script(
    context: BrowserContext,
    profile: dict[str, Any],
    logger
) -> None:
    page = context.pages[0]
    await page.goto(f"https://web.telegram.org/a")
    update_telegram_button: Locator = page.get_by_text(
        "update telegram"
    )
    try:
        await update_telegram_button.click(timeout=15000)
        await page.wait_for_timeout(5000)
    except Error:
        logger.success(
            "Telegram updated!",
            id=profile["id"]
        )
    else:
        logger.info(
            f"Telegram not updated",
            id=profile["id"]
        )


asyncio.run(script())
