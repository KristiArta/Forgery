import os
import json
import asyncio
from typing import Any, Callable, Iterable
from math import ceil
from playwright.async_api import Playwright, Error
from playwright.async_api import async_playwright
from src.core.utils import logger


def execute_chromium(
    profiles: str,
    config: str | dict[str, Any]
) -> None:
    def decorator(script: Callable):
        async def wrapper():
            USER: str = os.getlogin()
            assert USER
            async def execute(
                playwright: Playwright,
                profile: dict[str, Any],
                headless: bool | None,
                extensions: Iterable[str] | None,
                use_wayland: bool | None,
                device_model: str | None,
                devtools: bool | None
            ) -> None:
                proxy: dict | None = None
                device: dict = {}
                if profile.get("proxy"):
                    proxy = {
                        "server": profile["proxy"]["server"],
                        "username": profile["proxy"]["username"],
                        "password": profile["proxy"]["password"]
                    }
                args: list = [
                    "--no-first-run",
                    "--ignore-certificate-errors",
                    "--disable-blink-features=AutomationControlled",
                    "--webrtc-ip-handling-policy=disable_non_proxied_udp",
                    "--hide-crash-restore-bubble",
                    "--mute-audio",
                    "--test-type=browser"
                ]
                if use_wayland:
                    args.append("--enable-unsafe-webgpu")
                    args.append("--enable-features=UseOzonePlatform")
                    args.append("--ozone-platform=wayland")
                if extensions:
                    disabled_extensions: str = "--disable-extensions-except="
                    for extension in extensions:
                        disabled_extensions += f"{extension},"
                        args.append(
                            f"--load-extension={extension}"
                        )
                    args.append(disabled_extensions.removesuffix(","))
                if device_model:
                    device = playwright.devices[device_model]
                    device.pop("default_browser_type")
                profile_path: str = f"/home/{USER}/.config/chromium/{profile['id']}"
                try:
                    context = await playwright.chromium.launch_persistent_context(
                        profile_path,
                        ignore_default_args=(
                            "--enable-automation",
                            # "--remote-debugging-pipe"
                            # allows to bypass CDP detection,
                            # but breaks playwright functionality
                        ),
                        proxy=proxy,
                        devtools=devtools,
                        service_workers="block",
                        headless=headless,
                        args=args,
                        **device
                    )
                    logger.info(
                        "Context launched",
                        id=profile["id"]
                    )
                    # await context.add_init_script(
                    #     "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                    # )
                    await script(context, profile, logger)
                except Exception as e:
                    logger.error(
                        str(e) + "!",
                        id=profile["id"]
                    )
                finally:
                    msg: str
                    try:
                        await context.unroute_all(behavior='ignoreErrors')
                        await context.close()
                        msg = "Context closed"
                    except (UnboundLocalError, Error):
                        msg = "Context already closed"
                    logger.info(
                        msg,
                        id=profile["id"]
                    )

            async with async_playwright() as playwright:
                profiles_obj: list[dict[str, Any]]
                config_obj: dict[str, Any]
                if profiles:
                    with open(profiles, "r") as f:
                        profiles_obj = json.load(f)
                if isinstance(config, str):
                    with open(config, "r") as f:
                        config_obj = json.load(f)
                elif isinstance(config, dict):
                    config_obj = config
                if not config_obj.get("profile_ids"):
                    config_obj["profile_ids"] = [
                        profile["id"]
                        for profile 
                        in profiles_obj
                    ]
                if not config_obj.get("exclude_profile_ids"):
                    config_obj["exclude_profile_ids"] = []

                async def process_threaded_batch(
                    batch: list[dict[str, Any]],
                    **kwargs
                ) -> None:
                    for profile in batch:
                        await execute(
                            profile=profile,
                            **kwargs
                        )

                batch_tasks: list = []
                included_profiles: list[dict[str, Any]] = [
                    profile
                    for profile in profiles_obj
                    if (
                        profile["id"] in config_obj["profile_ids"]
                        and not profile["id"] in config_obj["exclude_profile_ids"]
                    )
                ]
                for threaded_batch in [
                    included_profiles[i::config_obj["threads"]]
                    for i in range(config_obj["threads"])
                ]:
                    batch_tasks.append(
                        asyncio.create_task(
                            process_threaded_batch(
                                threaded_batch,
                                playwright=playwright,
                                headless=config_obj.get("headless"),
                                extensions=config_obj.get("extensions"),
                                use_wayland=config_obj.get("use_wayland"),
                                device_model=config_obj.get("device_model"),
                                devtools=config_obj.get("devtools")
                            )
                        )
                    )
                if batch_tasks:
                    await asyncio.gather(*batch_tasks)

        return wrapper

    return decorator
