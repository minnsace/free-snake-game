"""Procedural rounded-square obstacles for an infinite, chunk-generated world.

The world is split into CHUNK_SIZE x CHUNK_SIZE cell chunks. Each chunk is
generated lazily, on demand, using a per-chunk RNG seeded from the chunk's
coordinates and a per-run world seed -- so a given chunk always generates the
same obstacles, but a fresh world seed gives a different layout each run.
"""

import random

from . import settings


def chunk_coord(col: int, row: int) -> tuple[int, int]:
    return col // settings.CHUNK_SIZE, row // settings.CHUNK_SIZE


def chunks_in_view(camera_col: float, camera_row: float, margin: int = settings.CHUNK_GEN_MARGIN):
    """Chunk coords covering the camera's viewport plus a generation margin."""
    pad = margin * settings.CHUNK_SIZE
    min_cx, min_cy = chunk_coord(int(camera_col) - pad, int(camera_row) - pad)
    max_cx, max_cy = chunk_coord(int(camera_col + settings.VIEW_W) + pad, int(camera_row + settings.VIEW_H) + pad)
    for cx in range(min_cx, max_cx + 1):
        for cy in range(min_cy, max_cy + 1):
            yield cx, cy


def generate_chunk(cx: int, cy: int, world_seed: int, spawn: tuple[int, int]) -> set[tuple[int, int]]:
    """Deterministically generate obstacle cells for one chunk.

    Shapes (singles, dominoes, L-triples, 2x2 blocks) are placed on an
    evenly-spaced anchor sub-grid rather than an independent per-cell coin
    flip -- this gives varied cluster silhouettes while keeping the overall
    layout orderly instead of chaotic single-cell noise.
    """
    rng = random.Random(f"{world_seed}:{cx}:{cy}")
    cells: set[tuple[int, int]] = set()
    base_col = cx * settings.CHUNK_SIZE
    base_row = cy * settings.CHUNK_SIZE
    sx, sy = spawn
    step = settings.OBSTACLE_ANCHOR_SPACING
    shapes = [shape for shape, _ in settings.OBSTACLE_SHAPES]
    weights = [weight for _, weight in settings.OBSTACLE_SHAPES]
    for lc in range(0, settings.CHUNK_SIZE, step):
        for lr in range(0, settings.CHUNK_SIZE, step):
            anchor_col, anchor_row = base_col + lc, base_row + lr
            if rng.random() >= settings.OBSTACLE_DENSITY:
                continue
            shape = rng.choices(shapes, weights=weights, k=1)[0]
            block_cells = [(anchor_col + dc, anchor_row + dr) for dc, dr in shape]
            if any(max(abs(c - sx), abs(r - sy)) <= settings.SAFE_SPAWN_RADIUS for c, r in block_cells):
                continue
            cells.update(block_cells)
    return cells
