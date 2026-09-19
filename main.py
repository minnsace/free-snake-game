"""Entry point. Uses an asyncio loop so it runs both natively and via pygbag."""

import asyncio
import random

import pygame

from game import settings, renderer
from game.snake import Snake
from game import obstacles as obstacles_mod
from game import orb as orb_mod
from game.input import (
    configure_web_display,
    direction_from_key,
    direction_from_touch,
    hide_web_splash,
    is_mobile_browser,
    web_viewport_aspect_ratio,
)


class Game:
    def __init__(self):
        pygame.init()
        self.touch_controls = is_mobile_browser()
        browser_aspect = web_viewport_aspect_ratio()
        if browser_aspect:
            settings.configure_viewport(browser_aspect)
        pygame.display.set_caption("Free Snake Game")
        self.window = pygame.display.set_mode((settings.WINDOW_W, settings.WINDOW_H))
        configure_web_display()
        # Draw straight to the window (no low-res upscale) -- avoids the
        # jittery/nauseating look that came from scaling up a scrolling scene.
        self.internal = self.window
        self.clock = pygame.time.Clock()
        # Pygame's bundled font renders consistently in desktop and WebAssembly.
        self.font = pygame.font.Font(None, 28)
        self.title_font = pygame.font.Font(None, 54)
        self.card_font = pygame.font.Font(None, 28)
        self.splash_hidden = False
        self.reset()

    def reset(self, start_immediately: bool = False):
        start = (0, 0)
        self.snake = Snake(start)
        self.world_seed = random.randint(0, 2**31 - 1)
        self.obstacles: set[tuple[int, int]] = set()
        self.generated_chunks: set[tuple[int, int]] = set()

        # Center the camera on the spawn point, then let it dead-zone-follow from there.
        self.camera_col = start[0] - settings.VIEW_W / 2
        self.camera_row = start[1] - settings.VIEW_H / 2
        self._generate_visible_chunks()

        self.orb = orb_mod.spawn(
            set(self.snake.body) | self.obstacles,
            self.obstacles,
            self.camera_col,
            self.camera_row,
            self.snake.head,
        )
        self.score = 0
        self.game_over = False
        self.started = start_immediately
        self.time_since_move = 0.0
        self.t = 0.0
        self.joystick_active = False
        self.joystick_finger_id = None
        self.joystick_position = settings.JOYSTICK_CENTER

    def _generate_visible_chunks(self) -> None:
        for cx, cy in obstacles_mod.chunks_in_view(self.camera_col, self.camera_row):
            if (cx, cy) in self.generated_chunks:
                continue
            self.generated_chunks.add((cx, cy))
            self.obstacles |= obstacles_mod.generate_chunk(cx, cy, self.world_seed, self.snake.body[0])

    def _update_camera(self, dt: float) -> None:
        """Dead-zone follow: only scroll once the head nears the viewport edge,
        then ease the camera back so the buffer is restored."""
        head_col, head_row = self.snake.head
        buf = settings.CAMERA_BUFFER
        target_col, target_row = self.camera_col, self.camera_row

        if head_col - target_col < buf:
            target_col = head_col - buf
        elif head_col - target_col > settings.VIEW_W - buf:
            target_col = head_col - (settings.VIEW_W - buf)

        if head_row - target_row < buf:
            target_row = head_row - buf
        elif head_row - target_row > settings.VIEW_H - buf:
            target_row = head_row - (settings.VIEW_H - buf)

        ease = min(1.0, dt * settings.CAMERA_SMOOTH)
        self.camera_col += (target_col - self.camera_col) * ease
        self.camera_row += (target_row - self.camera_row) * ease

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Return False to quit."""
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            if not self.started:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.started = True
                return True
            if self.game_over:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.reset(start_immediately=True)
                return True
            new_dir = direction_from_key(event.key)
            if new_dir:
                self.snake.set_direction(new_dir)
        if self.touch_controls:
            self._handle_touch_event(event)
        return True

    def _event_position(self, event: pygame.event.Event) -> tuple[float, float]:
        if event.type in (pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP):
            return event.x * settings.INTERNAL_W, event.y * settings.INTERNAL_H
        return event.pos

    def _update_joystick(self, position: tuple[float, float]) -> None:
        self.joystick_position = position
        direction = direction_from_touch(
            position,
            settings.JOYSTICK_CENTER,
            settings.JOYSTICK_DEAD_ZONE,
        )
        if direction:
            self.snake.set_direction(direction)

    def _handle_touch_event(self, event: pygame.event.Event) -> None:
        down_events = (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN)
        motion_events = (pygame.FINGERMOTION, pygame.MOUSEMOTION)
        up_events = (pygame.FINGERUP, pygame.MOUSEBUTTONUP)

        if event.type in down_events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button != 1:
                return
            if not self.started:
                self.started = True
                return
            if self.game_over:
                self.reset(start_immediately=True)
                return

            position = self._event_position(event)
            if pygame.Vector2(position).distance_to(settings.JOYSTICK_CENTER) > settings.JOYSTICK_ACTIVATION_RADIUS:
                return
            self.joystick_active = True
            self.joystick_finger_id = getattr(event, "finger_id", None)
            self._update_joystick(position)
            return

        if not self.joystick_active:
            return
        finger_id = getattr(event, "finger_id", None)
        if self.joystick_finger_id is not None and finger_id not in (None, self.joystick_finger_id):
            return
        if event.type in motion_events:
            self._update_joystick(self._event_position(event))
        elif event.type in up_events:
            self.joystick_active = False
            self.joystick_finger_id = None
            self.joystick_position = settings.JOYSTICK_CENTER

    def update(self, dt: float) -> None:
        if not self.started or self.game_over:
            return
        self.t += dt
        self._update_camera(dt)
        self._generate_visible_chunks()

        self.time_since_move += dt
        step_interval = 1.0 / settings.move_speed(self.score)
        if self.time_since_move < step_interval:
            return
        self.time_since_move -= step_interval

        new_head = self.snake.step()

        if self.snake.hits_self() or new_head in self.obstacles:
            self.game_over = True
            return

        if new_head == self.orb:
            self.snake.grow(1)
            self.score += 1
            self.orb = orb_mod.spawn(
                set(self.snake.body) | self.obstacles,
                self.obstacles,
                self.camera_col,
                self.camera_row,
                self.snake.head,
            )

    def draw(self) -> None:
        move_progress = min(1.0, self.time_since_move * settings.move_speed(self.score))
        rendered_body = self.snake.interpolated_body(move_progress)
        renderer.draw_background(self.internal)
        renderer.draw_obstacles(self.internal, self.obstacles, self.camera_col, self.camera_row)
        renderer.draw_orb(self.internal, self.orb, self.camera_col, self.camera_row, self.t)
        renderer.draw_snake(self.internal, rendered_body, self.camera_col, self.camera_row)
        renderer.draw_scent_pulse(
            self.internal,
            rendered_body[0],
            self.orb,
            self.camera_col,
            self.camera_row,
            self.t,
        )
        if self.touch_controls and self.started and not self.game_over:
            renderer.draw_joystick(
                self.internal,
                self.joystick_position,
                self.joystick_active,
            )
        renderer.draw_text_centered(self.internal, self.font, f"SCORE: {self.score}", 16)
        if self.game_over:
            renderer.draw_game_over_screen(
                self.internal,
                self.title_font,
                self.card_font,
                self.score,
                self.touch_controls,
            )
        elif not self.started:
            renderer.draw_start_screen(
                self.internal,
                self.title_font,
                self.card_font,
                self.touch_controls,
            )

        pygame.display.flip()
        if not self.splash_hidden:
            hide_web_splash()
            self.splash_hidden = True


async def main():
    game = Game()
    running = True
    while running:
        dt = game.clock.tick(settings.FPS) / 1000.0
        for event in pygame.event.get():
            running = game.handle_event(event)
        game.update(dt)
        game.draw()
        await asyncio.sleep(0)  # yield to browser event loop under pygbag

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
