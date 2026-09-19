"""Food orb spawning."""

from collections import deque
import random

from . import settings


_CARDINAL_DIRECTIONS = ((0, -1), (0, 1), (-1, 0), (1, 0))


def _reachable_cells(
    free: set[tuple[int, int]], origin: tuple[int, int]
) -> set[tuple[int, int]]:
    reachable: set[tuple[int, int]] = set()
    frontier = deque([origin])
    visited = {origin}
    while frontier:
        col, row = frontier.popleft()
        for dc, dr in _CARDINAL_DIRECTIONS:
            neighbor = (col + dc, row + dr)
            if neighbor in free and neighbor not in visited:
                visited.add(neighbor)
                reachable.add(neighbor)
                frontier.append(neighbor)
    return reachable


def spawn(
    blocked: set[tuple[int, int]],
    obstacles: set[tuple[int, int]],
    camera_col: float,
    camera_row: float,
    origin: tuple[int, int],
) -> tuple[int, int]:
    """Pick a reachable free cell within the current camera viewport."""
    margin = 2
    cols = range(int(camera_col) - margin, int(camera_col) + settings.VIEW_W + margin)
    rows = range(int(camera_row) - margin, int(camera_row) + settings.VIEW_H + margin)
    region = {(col, row) for col in cols for row in rows}
    traversable = region - obstacles
    candidates = _reachable_cells(traversable, origin) - blocked
    return random.choice(tuple(candidates)) if candidates else origin
