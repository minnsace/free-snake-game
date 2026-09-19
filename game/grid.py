"""World cell <-> screen pixel conversions, relative to a scrolling camera."""

from . import settings


def cell_to_screen_px(col: int, row: int, camera_col: float, camera_row: float) -> tuple[float, float]:
    """Top-left internal pixel coordinate of a world cell, camera-relative."""
    return (col - camera_col) * settings.CELL_PX, (row - camera_row) * settings.CELL_PX


def cell_center_screen_px(col: int, row: int, camera_col: float, camera_row: float) -> tuple[float, float]:
    """Center internal pixel coordinate of a world cell, camera-relative."""
    x, y = cell_to_screen_px(col, row, camera_col, camera_row)
    return x + settings.CELL_PX / 2, y + settings.CELL_PX / 2
