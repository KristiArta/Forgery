import asyncio
from random import uniform
from typing import Any
from argparse import ArgumentParser
from src.forgery.automation import execute_chromium
from playwright.async_api import BrowserContext, Error, APIResponse
from src.core.utils import MAX_TIMEOUT


parser = ArgumentParser(
    "browser",
    ""
)
parser.add_argument(
    "profile",
    type=str,
    help="identifier of a browser profile"
)
parser.add_argument(
    "-H", "--headless",
    action="store_true"
)
parser.add_argument(
    "-W", "--use_wayland",
    action="store_true"
)
parser.add_argument(
    "-e", "--extension",
    action="append",
    default=[],
    help="path to an extension folder"
)
parser.add_argument(
    "-d", "--device_model",
    type=str,
    help="model of a device to emulate"
)

args = parser.parse_args()


@execute_chromium(
    profiles="profiles.json",
    config={
        "profile_ids": [
            args.profile
        ],
        "threads": 1,
        "headless": args.headless,
        "use_wayland": args.use_wayland,
        "extensions": [
            *args.extension
        ],
        "device_model": args.device_model
    }
)
async def script(
    context: BrowserContext,
    profile: dict[str, Any],
    logger
) -> None:
    page = context.pages[0]
    await page.wait_for_timeout(MAX_TIMEOUT)


asyncio.run(script())
