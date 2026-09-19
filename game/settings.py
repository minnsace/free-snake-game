"""Central tuning knobs for the camera viewport, world generation, timing, and palette."""

# Default desktop viewport size in cells. Web builds adapt one axis to the
# browser's startup aspect ratio while preserving square cells.
VIEW_W = 30
VIEW_H = 20

# Pixels per cell, rendered directly at full resolution (no low-res upscale --
# that caused jittery/nauseating scrolling once the camera started moving).
CELL_PX = 32

WINDOW_W = VIEW_W * CELL_PX
WINDOW_H = VIEW_H * CELL_PX
INTERNAL_W = WINDOW_W
INTERNAL_H = WINDOW_H


def configure_viewport(aspect_ratio: float) -> None:
    global VIEW_W, VIEW_H, WINDOW_W, WINDOW_H, INTERNAL_W, INTERNAL_H

    aspect_ratio = max(0.48, min(2.1, aspect_ratio))
    if aspect_ratio >= 1.0:
        VIEW_H = 20
        VIEW_W = max(24, round(VIEW_H * aspect_ratio))
    else:
        VIEW_W = 20
        VIEW_H = max(24, round(VIEW_W / aspect_ratio))

    WINDOW_W = VIEW_W * CELL_PX
    WINDOW_H = VIEW_H * CELL_PX
    INTERNAL_W = WINDOW_W
    INTERNAL_H = WINDOW_H

FPS = 60
# Cells moved per second; independent of FPS so speed feels consistent.
# Each collected orb raises the pace slightly, with a cap for playability.
START_MOVE_SPEED = 5.0
SPEED_PER_ORB = 0.25
MAX_MOVE_SPEED = 10.0


def move_speed(score: int) -> float:
    return min(MAX_MOVE_SPEED, START_MOVE_SPEED + score * SPEED_PER_ORB)

# --- Camera (dead-zone follow) ---
# Cells of empty buffer kept between the snake head and the viewport edge;
# the camera only scrolls once the head breaches this buffer (classic
# platformer "dead-zone" camera trick).
CAMERA_BUFFER = 7
# How quickly the camera eases toward its target position (higher = snappier).
CAMERA_SMOOTH = 6.0

# --- Infinite world / obstacle generation ---
# World is split into CHUNK_SIZE x CHUNK_SIZE cell chunks, generated lazily
# with a deterministic per-chunk RNG as the camera approaches them.
CHUNK_SIZE = 10
# Obstacles are placed as small cell-cluster "shapes" on an evenly-spaced
# sub-grid (rather than an independent per-cell coin flip), matching the
# mix of singles/dominoes/L-shapes/2x2 blocks seen in the reference art.
# Each shape is a tuple of (dc, dr) offsets, all within a 2x2 footprint so
# they never overlap a neighboring anchor slot.
OBSTACLE_ANCHOR_SPACING = 2
OBSTACLE_SHAPES = [
    (((0, 0),), 5),                                   # single cell
    (((0, 0), (1, 0)), 3),                            # horizontal domino
    (((0, 0), (0, 1)), 3),                             # vertical domino
    (((1, 0), (0, 1), (1, 1)), 2),                     # L, missing top-left
    (((0, 0), (0, 1), (1, 1)), 2),                     # L, missing top-right
    (((0, 0), (1, 0), (1, 1)), 2),                     # L, missing bottom-left
    (((0, 0), (1, 0), (0, 1)), 2),                     # L, missing bottom-right
    (((0, 0), (1, 0), (0, 1), (1, 1)), 2),             # 2x2 block
]
OBSTACLE_DENSITY = 0.16
# Extra chunks generated beyond the visible viewport so new terrain never pops in.
CHUNK_GEN_MARGIN = 1
# Cells within this Chebyshev distance of the snake's spawn point stay clear.
SAFE_SPAWN_RADIUS = 6

# Snake body / food orb circle radius (uniform -- no tapering).
SNAKE_RADIUS = CELL_PX // 2 - 3
# Obstacle rounded-square corner radius -- small, so it reads as square, not round.
OBSTACLE_CORNER_RADIUS = 5

# --- Orb guidance ---
# The snake briefly tastes the air on this cadence and points toward the orb.
SCENT_INTERVAL = 3.0
SCENT_DURATION = 0.7
TONGUE_LENGTH = 19
TONGUE_WIDTH = 2
TONGUE_FORK_LENGTH = 5
TONGUE_CURVE = 3
SCENT_EDGE_INSET = 18
SCENT_DOT_RADIUS = 4
SCENT_DOT_SPACING = 10

# A breathing ring makes the orb distinct from the snake's uniform segments.
ORB_RING_MIN_RADIUS = SNAKE_RADIUS + 5
ORB_RING_MAX_RADIUS = SNAKE_RADIUS + 9
ORB_RING_WIDTH = 2
ORB_RING_SPEED = 2.0

BG = (46, 158, 96)
DARK_GREEN = (17, 46, 22)
TEXT_GREEN = (17, 46, 22)
CARD_BG = (10, 35, 18)
CARD_BORDER = (91, 205, 130)
CARD_TEXT = (218, 246, 226)
OVERLAY_SHADE = (4, 18, 9, 150)

# --- Mobile controls ---
JOYSTICK_RADIUS = 88
JOYSTICK_DEAD_ZONE = 12
JOYSTICK_KNOB_RADIUS = 28
JOYSTICK_EDGE_MARGIN = 14
JOYSTICK_AXIS_LOCK = 1.1
JOYSTICK_BASE_COLOR = (218, 246, 226, 62)
JOYSTICK_BORDER_COLOR = (218, 246, 226, 145)
JOYSTICK_KNOB_COLOR = (218, 246, 226, 185)
