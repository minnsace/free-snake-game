"""Drawing: obstacles, snake, orb guidance, and HUD text."""

import math

import pygame

from . import settings
from .grid import cell_center_screen_px, cell_to_screen_px


def draw_background(surface: pygame.Surface) -> None:
    surface.fill(settings.BG)


def draw_obstacles(surface: pygame.Surface, obstacles: set, camera_col: float, camera_row: float) -> None:
    for col, row in obstacles:
        x, y = cell_to_screen_px(col, row, camera_col, camera_row)
        if x < -settings.CELL_PX or y < -settings.CELL_PX or x > settings.INTERNAL_W or y > settings.INTERNAL_H:
            continue
        rect = pygame.Rect(round(x) + 1, round(y) + 1, settings.CELL_PX - 2, settings.CELL_PX - 2)
        pygame.draw.rect(surface, settings.DARK_GREEN, rect, border_radius=settings.OBSTACLE_CORNER_RADIUS)


def draw_snake(surface: pygame.Surface, body, camera_col: float, camera_row: float) -> None:
    """Every segment (including the head) is drawn at the same uniform size."""
    for col, row in body:
        center = cell_center_screen_px(col, row, camera_col, camera_row)
        center = (round(center[0]), round(center[1]))
        pygame.draw.circle(surface, settings.DARK_GREEN, center, settings.SNAKE_RADIUS)


def draw_orb(
    surface: pygame.Surface,
    cell: tuple[int, int],
    camera_col: float,
    camera_row: float,
    elapsed_time: float,
) -> None:
    center = cell_center_screen_px(*cell, camera_col, camera_row)
    center = (round(center[0]), round(center[1]))
    pygame.draw.circle(surface, settings.DARK_GREEN, center, settings.SNAKE_RADIUS)

    pulse = (math.sin(elapsed_time * math.tau * settings.ORB_RING_SPEED) + 1.0) / 2.0
    radius = round(
        settings.ORB_RING_MIN_RADIUS
        + pulse * (settings.ORB_RING_MAX_RADIUS - settings.ORB_RING_MIN_RADIUS)
    )
    pygame.draw.circle(surface, settings.DARK_GREEN, center, radius, settings.ORB_RING_WIDTH)


def _direction_between(start: tuple[float, float], end: tuple[float, float]) -> tuple[float, float] | None:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    distance = math.hypot(dx, dy)
    if distance == 0:
        return None
    return dx / distance, dy / distance


def _ray_to_inset_edge(
    start: tuple[float, float], direction: tuple[float, float], width: int, height: int
) -> tuple[float, float]:
    inset = settings.SCENT_EDGE_INSET
    dx, dy = direction
    distances = []
    if dx > 0:
        distances.append((width - inset - start[0]) / dx)
    elif dx < 0:
        distances.append((inset - start[0]) / dx)
    if dy > 0:
        distances.append((height - inset - start[1]) / dy)
    elif dy < 0:
        distances.append((inset - start[1]) / dy)
    distance = min(value for value in distances if value >= 0)
    return start[0] + dx * distance, start[1] + dy * distance


def draw_scent_pulse(
    surface: pygame.Surface,
    head_cell: tuple[int, int],
    orb_cell: tuple[int, int],
    camera_col: float,
    camera_row: float,
    elapsed_time: float,
) -> None:
    phase = elapsed_time % settings.SCENT_INTERVAL
    if phase >= settings.SCENT_DURATION:
        return

    head = cell_center_screen_px(*head_cell, camera_col, camera_row)
    orb = cell_center_screen_px(*orb_cell, camera_col, camera_row)
    direction = _direction_between(head, orb)
    if direction is None:
        return

    progress = phase / settings.SCENT_DURATION
    amount = math.sin(math.pi * progress)
    dx, dy = direction
    tongue_base = (
        head[0] + dx * (settings.SNAKE_RADIUS - 1),
        head[1] + dy * (settings.SNAKE_RADIUS - 1),
    )
    tongue_tip = (
        tongue_base[0] + dx * settings.TONGUE_LENGTH * amount,
        tongue_base[1] + dy * settings.TONGUE_LENGTH * amount,
    )
    perpendicular = (-dy, dx)
    bend = math.sin(progress * math.tau) * settings.TONGUE_CURVE * amount
    tongue_split = (
        tongue_tip[0] - dx * settings.TONGUE_FORK_LENGTH * amount,
        tongue_tip[1] - dy * settings.TONGUE_FORK_LENGTH * amount,
    )
    tongue_middle = (
        (tongue_base[0] + tongue_split[0]) / 2.0 + perpendicular[0] * bend,
        (tongue_base[1] + tongue_split[1]) / 2.0 + perpendicular[1] * bend,
    )
    base_px = (round(tongue_base[0]), round(tongue_base[1]))
    split_px = (round(tongue_split[0]), round(tongue_split[1]))
    pygame.draw.lines(
        surface,
        settings.DARK_GREEN,
        False,
        [base_px, (round(tongue_middle[0]), round(tongue_middle[1])), split_px],
        settings.TONGUE_WIDTH,
    )

    fork_length = settings.TONGUE_FORK_LENGTH * amount
    for side in (-1, 1):
        fork_end = (
            tongue_split[0] + dx * fork_length + perpendicular[0] * fork_length * 0.45 * side,
            tongue_split[1] + dy * fork_length + perpendicular[1] * fork_length * 0.45 * side,
        )
        pygame.draw.line(
            surface,
            settings.DARK_GREEN,
            split_px,
            (round(fork_end[0]), round(fork_end[1])),
            settings.TONGUE_WIDTH,
        )

    orb_is_onscreen = 0 <= orb[0] < surface.get_width() and 0 <= orb[1] < surface.get_height()
    if orb_is_onscreen:
        return

    edge = _ray_to_inset_edge(head, direction, surface.get_width(), surface.get_height())
    dot_radius = max(1, round(settings.SCENT_DOT_RADIUS * amount))
    for index in range(3):
        center = (
            round(edge[0] - dx * settings.SCENT_DOT_SPACING * index),
            round(edge[1] - dy * settings.SCENT_DOT_SPACING * index),
        )
        pygame.draw.circle(surface, settings.DARK_GREEN, center, max(1, dot_radius - index))


def draw_text_centered(surface: pygame.Surface, font: pygame.font.Font, text: str, y: int) -> None:
    img = font.render(text, True, settings.TEXT_GREEN)
    rect = img.get_rect(center=(surface.get_width() // 2, y))
    surface.blit(img, rect)


def _draw_card(surface: pygame.Surface, width: int, height: int) -> pygame.Rect:
    card = pygame.Rect(
        0,
        0,
        min(width, surface.get_width() - 48),
        min(height, surface.get_height() - 48),
    )
    card.center = surface.get_rect().center
    pygame.draw.rect(surface, settings.CARD_BORDER, card)
    pygame.draw.rect(surface, settings.CARD_BG, card.inflate(-4, -4))
    return card


def _draw_card_text(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    center: tuple[int, int],
    color: tuple[int, int, int] = settings.CARD_TEXT,
    max_width: int | None = None,
) -> None:
    image = font.render(text, True, color)
    if max_width and image.get_width() > max_width:
        scale = max_width / image.get_width()
        image = pygame.transform.smoothscale(
            image,
            (max_width, max(1, round(image.get_height() * scale))),
        )
    surface.blit(image, image.get_rect(center=center))


def draw_start_screen(
    surface: pygame.Surface,
    title_font: pygame.font.Font,
    body_font: pygame.font.Font,
    touch_controls: bool = False,
) -> None:
    card = _draw_card(surface, 620, 330)
    center_x = card.centerx
    text_width = card.width - 72
    _draw_card_text(surface, title_font, "FREE SNAKE", (center_x, card.top + 58), max_width=text_width)
    controls = "DRAG THE JOYSTICK TO STEER" if touch_controls else "ARROW KEYS OR WASD TO STEER"
    _draw_card_text(surface, body_font, controls, (center_x, card.top + 130), max_width=text_width)
    _draw_card_text(
        surface,
        body_font,
        "FOLLOW THE TONGUE TO FIND ORBS",
        (center_x, card.top + 172),
        max_width=text_width,
    )
    _draw_card_text(
        surface,
        body_font,
        "AVOID YOUR TAIL AND THE BLOCKS",
        (center_x, card.top + 214),
        max_width=text_width,
    )
    _draw_card_text(
        surface,
        body_font,
        "TAP SCREEN TO START" if touch_controls else "PRESS ENTER OR SPACE TO START",
        (center_x, card.bottom - 48),
        settings.CARD_BORDER,
        text_width,
    )


def draw_game_over_screen(
    surface: pygame.Surface,
    title_font: pygame.font.Font,
    body_font: pygame.font.Font,
    score: int,
    touch_controls: bool = False,
) -> None:
    card = _draw_card(surface, 500, 260)
    center_x = card.centerx
    text_width = card.width - 72
    _draw_card_text(surface, title_font, "GAME OVER", (center_x, card.top + 58), max_width=text_width)
    _draw_card_text(
        surface,
        body_font,
        f"FINAL SCORE: {score}",
        (center_x, card.top + 128),
        max_width=text_width,
    )
    _draw_card_text(
        surface,
        body_font,
        "TAP SCREEN TO RESTART" if touch_controls else "PRESS ENTER OR SPACE TO RESTART",
        (center_x, card.bottom - 50),
        settings.CARD_BORDER,
        text_width,
    )


def draw_joystick(
    surface: pygame.Surface,
    center_position: tuple[float, float],
    position: tuple[float, float],
) -> None:
    layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    center = pygame.Vector2(center_position)
    knob = pygame.Vector2(position)
    offset = knob - center
    max_offset = settings.JOYSTICK_RADIUS - settings.JOYSTICK_KNOB_RADIUS
    if offset.length_squared() > max_offset * max_offset:
        knob = center + offset.normalize() * max_offset

    center_px = (round(center.x), round(center.y))
    knob_px = (round(knob.x), round(knob.y))
    pygame.draw.circle(
        layer,
        settings.JOYSTICK_BASE_COLOR,
        center_px,
        settings.JOYSTICK_RADIUS,
    )
    pygame.draw.circle(
        layer,
        settings.JOYSTICK_BORDER_COLOR,
        center_px,
        settings.JOYSTICK_RADIUS,
        3,
    )
    pygame.draw.circle(
        layer,
        settings.JOYSTICK_KNOB_COLOR,
        knob_px,
        settings.JOYSTICK_KNOB_RADIUS,
    )
    surface.blit(layer, (0, 0))
