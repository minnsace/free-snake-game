# Free Snake Game

A green pixel-art, infinite-world Snake built in Python + [pygame-ce](https://pyga.me/),
compiled to WebAssembly with [pygbag](https://github.com/pygame-web/pygbag) so it runs
directly in the browser at freesnakegame.com.

## Design

- **Grid-based world.** Everything (snake, orbs, obstacles) lives on `(col, row)`
  world coordinates (`game/grid.py`); pixels are only computed at draw time,
  relative to the camera.
- **Infinite open world, camera-followed.** There's no border and no wraparound
  — the world extends forever in every direction. A dead-zone camera
  (`Game._update_camera` in `main.py`) only scrolls once the snake's head
  breaches a buffer zone near the viewport edge, then eases back to restore
  that buffer, so the snake always has open space around it.
- **Lazy chunk generation.** The world is split into fixed-size chunks
  (`game/obstacles.py`); each chunk is generated on demand (with a
  deterministic per-chunk RNG) as the camera approaches it, so new terrain
  never pops in and memory only grows with explored area.
- **Procedural obstacles.** Obstacles are flat, dark-green rounded-rect
  "cubes" scattered at low density per chunk, always kept clear of the
  snake's spawn point.
- **Reachable orbs.** Orb candidates are flood-filled from the snake's head,
  so food cannot appear inside an obstacle-enclosed pocket.
- **Scent guidance.** Every few seconds the snake briefly flicks a forked
  tongue toward the food orb. If the orb is beyond the viewport, temporary
  scent dots mark the relevant screen edge; onscreen, a breathing ring makes
  the orb distinct from the snake without changing the monochrome palette.
- **Clear game flow.** A start screen explains steering and the objective
  before movement begins. After a collision, an opaque game-over card keeps
  the final score and restart prompt readable over the frozen board.
- **Rising difficulty.** The snake begins at a forgiving pace and speeds up
  slightly with each collected orb, capped so late-game steering remains
  playable as the body grows.
- **Responsive steering.** Rapid direction changes are buffered in order, and
  visual interpolation smooths movement between the underlying grid steps.
- **Mobile browser support.** Touch-capable mobile browsers get tap-to-start
  and tap-to-restart prompts plus a translucent drag joystick. The canvas keeps
  its 3:2 aspect ratio and scales to fit portrait or landscape viewports.
- **Retro pixel aesthetic.** The scene renders directly at the window's
  cell-aligned resolution. Snake segments and food orbs share the same solid
  circle shape and color, while the orb's animated ring provides recognition.

## Project layout

```
main.py             # entry point / game loop (asyncio, pygbag-compatible)
game/
  settings.py        # viewport size, camera, chunk/obstacle tuning, colors
  grid.py            # cell <-> camera-relative screen pixel conversion
  snake.py           # segment deque, movement, growth, self-collision
  obstacles.py        # chunk-based lazy procedural obstacle generation
  orb.py              # food spawn logic (within current camera viewport)
  renderer.py         # all drawing: circles, glow, rounded rects, HUD text
  input.py             # keyboard -> direction mapping
```

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Desktop controls: Enter/Space to start, arrow keys/WASD to steer, and
Enter/Space to restart after game over.

Mobile controls: tap to start, drag the lower-left joystick to steer, and tap
to restart after game over.

## Build for the web (pygbag)

```powershell
python tools/build_web.py
```

This creates a clean staging directory, runs pygbag, and produces a static
`build/web/` folder. The game runs entirely client-side with no server logic.

To preview the production artifact locally:

```powershell
python -m http.server 8000 --directory build/web
```

Then open `http://localhost:8000`.

## GitHub Pages

Pushing `main` runs `.github/workflows/deploy-pages.yml`, builds the pygbag
artifact, and publishes it with GitHub's official Pages actions. The tracked
`CNAME` configures the production domain as `freesnakegame.com`.

In the repository's **Settings > Pages**, select **GitHub Actions** as the
source. Configure these DNS records at the domain registrar:

| Host | Type | Value |
| --- | --- | --- |
| `@` | `A` | `185.199.108.153` |
| `@` | `A` | `185.199.109.153` |
| `@` | `A` | `185.199.110.153` |
| `@` | `A` | `185.199.111.153` |
| `www` | `CNAME` | `minnsace.github.io` |

After DNS resolves, enable **Enforce HTTPS** in the Pages settings.

## Deploy checklist

1. `python tools/build_web.py`
2. Push `main` and confirm the **Deploy GitHub Pages** workflow succeeds.
3. Confirm `https://minnsace.github.io/free-snake-game/` loads.
4. Update the DNS records and wait for `freesnakegame.com` to resolve.
5. Verify keyboard controls on desktop and tap/joystick controls on a real
  iOS or Android browser.
