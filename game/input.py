"""Keyboard input -> snake direction."""

import math
import sys

import pygame

from . import settings
from .snake import UP, DOWN, LEFT, RIGHT

_KEY_MAP = {
    pygame.K_UP: UP,
    pygame.K_w: UP,
    pygame.K_DOWN: DOWN,
    pygame.K_s: DOWN,
    pygame.K_LEFT: LEFT,
    pygame.K_a: LEFT,
    pygame.K_RIGHT: RIGHT,
    pygame.K_d: RIGHT,
}


def direction_from_key(key: int):
    return _KEY_MAP.get(key)


def direction_from_touch(
    position: tuple[float, float],
    center: tuple[float, float],
    dead_zone: float,
    current_direction=None,
    axis_lock: float = 1.0,
):
    dx = position[0] - center[0]
    dy = position[1] - center[1]
    if math.hypot(dx, dy) <= dead_zone:
        return None
    if current_direction in (LEFT, RIGHT) and abs(dy) <= abs(dx) * axis_lock:
        return RIGHT if dx > 0 else LEFT
    if current_direction in (UP, DOWN) and abs(dx) <= abs(dy) * axis_lock:
        return DOWN if dy > 0 else UP
    if abs(dx) > abs(dy):
        return RIGHT if dx > 0 else LEFT
    return DOWN if dy > 0 else UP


def is_mobile_browser() -> bool:
    if sys.platform != "emscripten":
        return False

    from platform import window

    user_agent = str(window.navigator.userAgent).lower()
    coarse_pointer = bool(window.matchMedia("(pointer: coarse)").matches)
    mobile_agent = any(name in user_agent for name in ("android", "iphone", "ipad", "mobile"))
    return coarse_pointer or mobile_agent


def web_viewport_aspect_ratio() -> float | None:
    if sys.platform != "emscripten":
        return None

    from platform import window

    width = max(1.0, float(window.innerWidth))
    height = max(1.0, float(window.innerHeight))
    return width / height


def configure_web_display() -> None:
    if sys.platform != "emscripten":
        return

    from platform import document

    viewport = document.querySelector('meta[name="viewport"]')
    if not viewport:
        viewport = document.createElement("meta")
        viewport.setAttribute("name", "viewport")
        document.head.appendChild(viewport)
    viewport.setAttribute(
        "content",
        "width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover",
    )

    board_color = "#2e9e60"
    document.documentElement.style.background = board_color
    document.documentElement.style.overflow = "hidden"
    document.body.style.margin = "0"
    document.body.style.width = "100vw"
    document.body.style.height = "100dvh"
    document.body.style.display = "flex"
    document.body.style.alignItems = "center"
    document.body.style.justifyContent = "center"
    document.body.style.background = board_color
    document.body.style.overflow = "hidden"

    canvas = document.querySelector("canvas")
    if canvas:
        aspect_ratio = settings.INTERNAL_W / settings.INTERNAL_H
        canvas.style.width = f"max(100vw, {aspect_ratio * 100}dvh)"
        canvas.style.height = f"max(100dvh, {100 / aspect_ratio}vw)"
        canvas.style.maxWidth = "none"
        canvas.style.maxHeight = "none"
        canvas.style.imageRendering = "pixelated"
        canvas.style.touchAction = "none"


def hide_web_splash() -> None:
    if sys.platform != "emscripten":
        return

    from platform import document

    splash = document.getElementById("minnsace-splash")
    if splash:
        splash.classList.add("is-hidden")
