from typing import Any
from io import BytesIO
import asyncio
from random import shuffle, choice
from time import time
from PIL import Image
from PIL import ImageColor
from src.forgery.automation import execute_chromium
from playwright.async_api import BrowserContext, expect, Locator, FrameLocator, Error, Route


class Px:
    def __init__(
        self,
        image_w: int,
        x: int,
        y: int,
        rgb: tuple,
        offset: tuple[int, int] = (0, 0)
    ) -> None:
        self.x = x + offset[0]
        self.y = y + offset[1]
        self.idx = self.y*image_w + self.x+1
        self.r, self.g, self.b = rgb[:3]
        self.color_hex = f"#{self.r:02x}{self.g:02x}{self.b:02x}".upper()


async def get_paintable_pixels(
    image: bytes,
    template: bytes,
    template_offset: tuple[int, int],
    limit: int
) -> list[Px]:
    result = []
    image = Image.open(BytesIO(image))
    template = Image.open(BytesIO(template))
    cropped_image = image.crop(
        (
            template_offset[0],
            template_offset[1],
            template_offset[0]+template.width,
            template_offset[1]+template.height
        )
    )
    assert cropped_image.width == template.width
    assert cropped_image.height == template.height
    xs = list(range(cropped_image.width))
    ys = list(range(cropped_image.height))
    shuffle(xs)
    shuffle(ys)
    for x in xs:
        for y in ys:
            t_px = Px(
                image.width,
                x,
                y,
                template.getpixel((x, y)),
                template_offset
            )
            i_px = Px(
                image.width,
                x,
                y,
                cropped_image.getpixel((x, y)),
                template_offset
            )
            if t_px.color_hex != i_px.color_hex:
                result.append(t_px)
                if len(result) == limit:
                    return result
    return result


@execute_chromium(
    profiles="profiles.json",
    config="scripts/notpixel/claimer/config.json"
)
async def script(
    context: BrowserContext,
    profile: dict[str, Any],
    logger
) -> None:
    async def route_repaint_start(
        route: Route,
    ):
        try:
            post_data = route.request.post_data_json
            if post_data:
                px = pxs.pop()
                post_data["newColor"] = px.color_hex
                post_data["pixelId"] = px.idx
                await route.continue_(
                    post_data=post_data
                )
        except Error:
            logger.warning(
                "Context is closed, routing failed!",
                id=profile["id"]
            )

    page = context.pages[0]
    await page.route(
        "https://notpx.app/api/v1/repaint/start",
        route_repaint_start
    )
    TEMPLATES = (
        ("1353629816", (36, 793)),
        ("6355200889", (75, 506)),
        ("1750502312", (493, 913)),
        ("305094295", (844, 683)),
        ("6597594922", (400, 1)),
        ("1166266887", (826, 268)),
        ("355876562", (800, 800))
    )
    template = choice(TEMPLATES)
    await page.goto(
        f"https://web.telegram.org/a/#?tgaddr=tg%3A%2F%2Fresolve%3Fdomain%3Dnotpixel%26appname%3Dapp%26startapp%3Df{template[0]}_t"
    )
    confirm_launch_button: Locator = page.get_by_role(
        "button",
        name="Confirm",
        exact=True
    )
    app_iframe: Locator = page.get_by_title(
        text="not pixel web app"
    )
    app_frame: FrameLocator
    try:
        await confirm_launch_button.click(
            timeout=10000
        )
        logger.info(
            "App launch confirmed",
            id=profile["id"]
        )
    except Error: pass
    try:
        await expect(app_iframe).to_be_visible(
            timeout=10000
        )
        app_frame = app_iframe.content_frame
    except AssertionError:
        logger.error(
            "App frame not found",
            id=profile["id"]
        )
        return
    else:
        logger.info(
            "App frame found",
            id=profile["id"]
        )
    proceed_button: Locator = app_frame.get_by_role(
        "button",
        name="Okay, promise",
        exact=True
    )
    proceed_further_button: Locator = app_frame.get_by_role(
        "button",
        name="Let’s Gooooooo!",
        exact=True
    )
    canvas: Locator = app_frame.locator(
        "xpath=/html/body/canvas"
    )
    paint_span: Locator = app_frame.get_by_text(
        "Paint"
    )
    energy_span: Locator = app_frame.locator(
        "xpath=/html/body/div[1]/div/div[7]/div/button/div[1]/div/div[2]/span[2]"
    )
    menu_button: Locator = app_frame.locator(
        "xpath=/html/body/div[1]/div/div[1]/div/div[2]/div[2]/button"
    )
    claim_span: Locator = app_frame.get_by_role(
        "button",
        name="Claim"
    )
    boosts_div: Locator = app_frame.get_by_text(
        "Boosts",
        exact=True
    )
    paint_reward_boost: Locator = app_frame.locator(
        "xpath=/html/body/div[1]/div/div[2]/div[2]/div[6]/div/div[2]/div[1]"
    )
    recharging_speed_boost: Locator = app_frame.locator(
        "xpath=/html/body/div[1]/div/div[2]/div[2]/div[6]/div/div[2]/div[2]"
    )
    energy_limit_boost: Locator = app_frame.locator(
        "xpath=/html/body/div[1]/div/div[2]/div[2]/div[6]/div/div[2]/div[3]"
    )
    buy_for_button: Locator = app_frame.get_by_role(
        "button",
        name="Buy for"
    )
    fail_popup: Locator = app_frame.get_by_text(
        "not enough px"
    )
    success_popup: Locator = app_frame.get_by_text(
        "well done"
    )
    try:
        await proceed_button.click(timeout=10000)
        logger.info(
            "Pop-up closed",
            id=profile["id"]
        )
    except Error: pass
    try:
        await proceed_further_button.click(timeout=10000)
        logger.success(
            "Game entered!",
            id=profile["id"]
        )
    except Error: pass
    await canvas.wait_for()
    canvas_rect = await canvas.bounding_box()
    await page.mouse.click(
        canvas_rect["x"] + int(canvas_rect["width"]/2),
        canvas_rect["y"] + int(canvas_rect["height"]/2)
    )
    energy = int(await energy_span.inner_text())
    if energy:
        # NOTE: Need to dispose of the request context?
        requester = page.request
        image = await (await requester.get("https://image.notpx.app/api/v2/image")).body()
        # template = await (await requester.get("https://app.notpx.app/assets/durovoriginal-CqJYkgok.png")).body()
        template_image = await (await requester.get(f"https://static.notpx.app/templates/{template[0]}.png")).body()
        pxs = await get_paintable_pixels(
            image,
            template_image,
            template[1],
            limit=energy
        )
        for _ in range(energy):
            await paint_span.click()
            await page.wait_for_timeout(500)
        logger.success(
            f"Energy points used: {energy}!",
            id=profile["id"]
        )
    else:
        logger.info(
            "No energy",
            id=profile["id"]
        )
    try: await menu_button.click()
    except Error:
        logger.error(
            "Menu not entered!",
            id=profile["id"]
        )
        return
    try: await claim_span.click(timeout=10000)
    except Error:
        logger.info(
            "Claim unavailable",
            id=profile["id"]
        )
    else:
        logger.success(
            "Points claimed!",
            id=profile["id"]
        )
    # try:
    #     await app_frame.locator("xpath=/html/body/div[1]/div/div[2]/div[2]/div[6]/div/div[1]/div").click()
    #     await page.get_by_text("Cancel").click()
    #     await app_frame.locator("xpath=/html/body/div[1]/div/div[2]/div[2]/div[6]/div/div[1]/div").click()
    #     await success_popup.wait_for()
    #     logger.success(
    #         "Advertisement bonus claimed!",
    #         id=profile["id"]
    #     )
    # except Error: pass
    await boosts_div.click()
    boosts: int = 0
    unavail = []
    while True:
        for boost in (
            paint_reward_boost,
            energy_limit_boost,
            recharging_speed_boost
        ):
            if boost not in unavail:
                try:
                    await boost.click(timeout=5000)
                    await buy_for_button.click(timeout=5000)
                    await buy_for_button.wait_for(state="detached")
                    await page.wait_for_timeout(500)
                    if await fail_popup.first.is_visible():
                        unavail.append(boost)
                        await fail_popup.first.wait_for(state="detached")
                    elif await success_popup.first.is_visible():
                        await success_popup.first.wait_for(state="detached")
                        boosts += 1
                except Error:
                    unavail.append(boost)
        if len(unavail) == 3:
            break
    if boosts:
        logger.success(
            f"Boosts made: {boosts}",
            id=profile["id"]
        )


asyncio.run(script())
