"""Snake state: segment list, movement, growth, collision checks."""

from collections import deque

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

_OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}


class Snake:
    def __init__(self, start: tuple[int, int], length: int = 4):
        col, row = start
        # Body is a deque of (col, row), head at index 0.
        self.body = deque((col - i, row) for i in range(length))
        self.direction = RIGHT
        self._direction_queue: deque[tuple[int, int]] = deque()
        self.previous_body = list(self.body)
        self.growth_pending = 0

    @property
    def head(self) -> tuple[int, int]:
        return self.body[0]

    def set_direction(self, new_dir: tuple[int, int]) -> None:
        """Buffer a turn, ignoring duplicates and 180-degree reversals."""
        last_direction = self._direction_queue[-1] if self._direction_queue else self.direction
        if new_dir == last_direction:
            return
        if new_dir == _OPPOSITE.get(last_direction) and len(self.body) > 1:
            return
        if len(self._direction_queue) < 3:
            self._direction_queue.append(new_dir)

    def set_touch_direction(self, new_dir: tuple[int, int]) -> bool:
        """Use the latest legal joystick turn instead of retaining stale input."""
        if new_dir == self.direction:
            self._direction_queue.clear()
            return True
        if new_dir == _OPPOSITE.get(self.direction) and len(self.body) > 1:
            return False
        self._direction_queue.clear()
        self._direction_queue.append(new_dir)
        return True

    def grow(self, amount: int = 1) -> None:
        self.growth_pending += amount

    def step(self) -> tuple[int, int]:
        """Advance one grid cell in the current direction. Returns new head."""
        self.previous_body = list(self.body)
        if self._direction_queue:
            self.direction = self._direction_queue.popleft()
        dx, dy = self.direction
        head_col, head_row = self.head
        new_head = (head_col + dx, head_row + dy)
        self.body.appendleft(new_head)
        if self.growth_pending > 0:
            self.growth_pending -= 1
        else:
            self.body.pop()
        return new_head

    def interpolated_body(self, progress: float) -> list[tuple[float, float]]:
        """Blend the previous grid state toward the current one for rendering."""
        progress = max(0.0, min(1.0, progress))
        previous_tail = self.previous_body[-1]
        return [
            (
                old_col + (new_col - old_col) * progress,
                old_row + (new_row - old_row) * progress,
            )
            for (new_col, new_row), (old_col, old_row) in zip(
                self.body,
                self.previous_body + [previous_tail] * (len(self.body) - len(self.previous_body)),
            )
        ]

    def hits_self(self) -> bool:
        head = self.head
        return head in list(self.body)[1:]

    def occupies(self, cell: tuple[int, int]) -> bool:
        return cell in self.body
