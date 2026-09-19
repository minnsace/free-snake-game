"""Keyboard input -> snake direction."""

import math
import sys

import pygame

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
):
    dx = position[0] - center[0]
    dy = position[1] - center[1]
    if math.hypot(dx, dy) <= dead_zone:
        return None
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

    document.documentElement.style.background = "#082311"
    document.documentElement.style.overflow = "hidden"
    document.body.style.margin = "0"
    document.body.style.width = "100vw"
    document.body.style.height = "100dvh"
    document.body.style.display = "flex"
    document.body.style.alignItems = "center"
    document.body.style.justifyContent = "center"
    document.body.style.background = "#082311"
    document.body.style.overflow = "hidden"

    canvas = document.querySelector("canvas")
    if canvas:
        canvas.style.width = "min(100vw, 150dvh)"
        canvas.style.height = "auto"
        canvas.style.maxHeight = "100dvh"
        canvas.style.imageRendering = "pixelated"
        canvas.style.touchAction = "none"
