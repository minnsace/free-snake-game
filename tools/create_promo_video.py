"""Capture the live game and create a LinkedIn-ready promotional MP4."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import textwrap
import time

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "promo" / "free-snake-game-linkedin.mp4"
SITE = "https://freesnakegame.com/"
FPS = 12
SIZE = (1080, 1350)
BG = (10, 35, 18)
BOARD = (46, 158, 96)
INK = (218, 246, 226)
ACCENT = (91, 205, 130)
DARK = (17, 46, 22)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "consolab.ttf" if bold else "consola.ttf"
    path = Path("C:/Windows/Fonts") / name
    return ImageFont.truetype(str(path), size)


def clean_driver(width: int, height: int, mobile: bool = False) -> webdriver.Edge:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument(f"--window-size={width},{height}")
    if mobile:
        options.add_argument(
            "--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1"
        )
    driver = webdriver.Edge(options=options)
    if mobile:
        driver.execute_cdp_cmd(
            "Emulation.setTouchEmulationEnabled", {"enabled": True, "maxTouchPoints": 5}
        )
    return driver


def wait_for_game(driver: webdriver.Edge) -> None:
    driver.get(f"{SITE}?promo={time.time_ns()}")
    WebDriverWait(driver, 60).until(
        lambda browser: "is-hidden"
        in browser.find_element(By.ID, "minnsace-splash").get_attribute("class")
    )
    time.sleep(0.4)


def screenshot(driver: webdriver.Edge) -> Image.Image:
    return Image.open(BytesIO(driver.get_screenshot_as_png())).convert("RGB")


def capture_footage() -> tuple[Image.Image, list[Image.Image], Image.Image]:
    driver = clean_driver(1200, 800)
    try:
        wait_for_game(driver)
        start = screenshot(driver)
        canvas = driver.find_element(By.ID, "canvas")
        canvas.click()
        canvas.send_keys(Keys.ENTER)

        directions = [
            (1.0, Keys.ARROW_DOWN),
            (2.0, Keys.ARROW_LEFT),
            (4.0, Keys.ARROW_UP),
            (6.0, Keys.ARROW_RIGHT),
            (8.0, Keys.ARROW_DOWN),
        ]
        footage: list[Image.Image] = []
        started = time.perf_counter()
        next_direction = 0
        duration = 9.0
        while time.perf_counter() - started < duration:
            elapsed = time.perf_counter() - started
            while next_direction < len(directions) and elapsed >= directions[next_direction][0]:
                canvas.send_keys(directions[next_direction][1])
                next_direction += 1
            footage.append(screenshot(driver))
            target = started + len(footage) / FPS
            delay = target - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
    finally:
        driver.quit()

    mobile_driver = clean_driver(390, 844, mobile=True)
    try:
        wait_for_game(mobile_driver)
        mobile = screenshot(mobile_driver)
    finally:
        mobile_driver.quit()

    return start, footage, mobile


def fit_image(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    scale = max(target_w / image.width, target_h / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - target_w) // 2
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def base_frame() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", SIZE, BG)
    draw = ImageDraw.Draw(image)
    for x in range(0, SIZE[0], 32):
        draw.line((x, 0, x, SIZE[1]), fill=(12, 48, 24), width=1)
    for y in range(0, SIZE[1], 32):
        draw.line((0, y, SIZE[0], y), fill=(12, 48, 24), width=1)
    return image, draw


def centered(draw: ImageDraw.ImageDraw, text: str, y: int, face: ImageFont.FreeTypeFont, color=INK) -> int:
    box = draw.textbbox((0, 0), text, font=face)
    x = (SIZE[0] - (box[2] - box[0])) // 2
    draw.text((x, y), text, font=face, fill=color)
    return y + box[3] - box[1]


def wrapped_centered(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    face: ImageFont.FreeTypeFont,
    width: int,
    color=INK,
    spacing: int = 10,
) -> int:
    average = max(1, draw.textlength("M", font=face))
    lines = textwrap.wrap(text, width=max(1, int(width / average)))
    for line in lines:
        y = centered(draw, line, y, face, color) + spacing
    return y


def gameplay_frame(source: Image.Image, headline: str, subline: str = "") -> Image.Image:
    image, draw = base_frame()
    centered(draw, "FREE SNAKE GAME", 52, font(24, True), ACCENT)
    wrapped_centered(draw, headline, 104, font(46, True), 940)
    if subline:
        wrapped_centered(draw, subline, 226, font(26), 900, ACCENT, 5)

    game = fit_image(source, (1000, 667))
    image.paste(game, (40, 330))
    draw.rectangle((38, 328, 1041, 998), outline=ACCENT, width=4)
    centered(draw, "freesnakegame.com", 1100, font(42, True), INK)
    centered(draw, "Built with Microsoft Paint + GitHub Copilot", 1180, font(22), ACCENT)
    return image


def intro_frame(progress: float) -> Image.Image:
    image, draw = base_frame()
    centered(draw, "I IMPULSIVELY BOUGHT", 235, font(46, True), INK)
    centered(draw, "freesnakegame.com", 330, font(65, True), ACCENT)
    centered(draw, "FOR $5", 440, font(78, True), INK)
    wrapped_centered(draw, "Then I realized I should probably put something on it.", 600, font(32), 840)
    x = 150 + round(progress * 620)
    y = 850
    for offset in range(0, 128, 32):
        draw.ellipse((x - offset - 13, y - 13, x - offset + 13, y + 13), fill=ACCENT)
    draw.ellipse((x - 13, y - 13, x + 13, y + 13), fill=INK)
    return image


def outro_frame(progress: float) -> Image.Image:
    image, draw = base_frame()
    centered(draw, "PLAY IT NOW", 300, font(58, True), INK)
    centered(draw, "freesnakegame.com", 420, font(68, True), ACCENT)
    wrapped_centered(draw, "All because I spent $5 on a domain before having a plan for it.", 610, font(32), 850)
    draw.rectangle((170, 850, 910, 858), fill=(17, 70, 33))
    draw.rectangle((170, 850, 170 + round(740 * progress), 858), fill=ACCENT)
    centered(draw, "Python  |  pygame-ce  |  WebAssembly", 1000, font(24), INK)
    return image


def write_video(start: Image.Image, footage: list[Image.Image], mobile: Image.Image) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    writer = imageio.get_writer(
        OUTPUT,
        fps=FPS,
        codec="libx264",
        quality=8,
        pixelformat="yuv420p",
        macro_block_size=2,
        output_params=["-movflags", "+faststart"],
    )
    try:
        for index in range(2 * FPS):
            writer.append_data(np.asarray(intro_frame(index / (2 * FPS - 1))))

        start_card = gameplay_frame(start, "So I made a game for it.", "Sketched in Paint. Built with GitHub Copilot.")
        for _ in range(2 * FPS):
            writer.append_data(np.asarray(start_card))

        segments = [
            ("It is Snake in an infinite world.", "The camera follows you wherever you go."),
            ("Food can end up outside your view.", "That made finding it way harder than I expected."),
            ("So the snake uses scent to help.", "Its tongue and edge markers point toward the food."),
        ]
        frames_per_segment = max(1, len(footage) // len(segments))
        for index, source in enumerate(footage):
            segment = min(len(segments) - 1, index // frames_per_segment)
            writer.append_data(np.asarray(gameplay_frame(source, *segments[segment])))

        mobile_card = gameplay_frame(
            mobile,
            "It works on phones too.",
            "Touch anywhere, drag the joystick, and let go to hide it.",
        )
        for _ in range(2 * FPS):
            writer.append_data(np.asarray(mobile_card))

        for index in range(2 * FPS):
            writer.append_data(np.asarray(outro_frame(index / (2 * FPS - 1))))
    finally:
        writer.close()


if __name__ == "__main__":
    start_screen, gameplay, mobile_screen = capture_footage()
    write_video(start_screen, gameplay, mobile_screen)
    print(f"Created {OUTPUT}")
