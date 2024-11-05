import asyncio
from typing import Any
from src.forgery.automation import execute_chromium
from playwright.async_api import BrowserContext, ElementHandle, Locator


@execute_chromium(
    profiles="profiles.json",
    config="scripts/telegram/authorizer/config.json"
)
async def script(
    context: BrowserContext,
    profile: dict[str, Any],
    logger
) -> None:
    page = context.pages[0]
    search_bar: Locator = page.get_by_placeholder(
        "search"
    )
    log_in_by_phone_button: Locator = page.get_by_role(
        "button",
        name="log in by phone number"
    )
    phone_input: Locator = page.get_by_label(
        "your phone number"
    )
    submit_phone_button: Locator = page.get_by_role(
        "button",
        name="Next"
    )
    code_input: Locator = page.get_by_label(
        "code"
    )
    password_input: Locator = page.locator(
        "//*[@id='sign-in-password']"
    )
    submit_password: Locator = page.get_by_role(
        "button",
        name="Next"
    )

    await page.goto("https://web.telegram.org/a")
    while True:
        await page.wait_for_timeout(500)
        if await search_bar.all():
            return
        elif await log_in_by_phone_button.all():
            break
    await log_in_by_phone_button.click()
    await phone_input.fill(
        "+" + profile["phone"]
    )
    await submit_phone_button.click()
    logger.info(
        "Phone submitted",
        id=profile["id"]
    )
    await code_input.fill(
        input(f"Enter an authentication code for {profile['id']}: ")
    )
    if profile["telegram"].get("password"):
        await password_input.fill(
            profile["telegram"]["password"]
        )
        await submit_password.click()
        logger.info(
            "Password submitted",
            id=profile["id"]
        )
    while True:
        await page.wait_for_timeout(500)
        if await search_bar.all():
            await page.wait_for_timeout(5000)
            logger.success(
                "Authorized!",
                id=profile["id"]
            )
            return


asyncio.run(script())
