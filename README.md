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
  the final score and restart prompt readable without dimming the frozen board.
- **Rising difficulty.** The snake begins at a forgiving pace and speeds up
  slightly with each collected orb, capped so late-game steering remains
  playable as the body grows.
- **Responsive steering.** Rapid direction changes are buffered in order, and
  visual interpolation smooths movement between the underlying grid steps.
- **Mobile browser support.** Touch-capable mobile browsers get tap-to-start
  and tap-to-restart prompts plus a translucent joystick that appears under the
  player's thumb. A small dead zone, light direction hysteresis, and latest-turn
  input keep it responsive without changing desktop keyboard steering. Web
  builds adapt the visible grid to wide, standard, or portrait browser aspect
  ratios while preserving square cells.
- **Polished web shell.** A branded `minnsace` splash covers pygbag startup,
  and pygame's bundled font keeps menu text stable across desktop and WASM.
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

Mobile controls: tap to start, then touch anywhere to place and drag the
joystick. Release to hide it; tap to restart after game over.

## Browser voice chat

The web build includes a public, shared voice room. Open the game or the
`voice.html` page on the same hostname on both devices. On the computer,
click **Enable alerts / test sound** and verify that you hear the test.
On the phone, click **Join voice chat** and allow microphone access.
Visitors with alerts enabled hear a repeating sound every five seconds while
someone is in voice chat and they have not joined. Click **Join voice chat**
on the computer to answer. **Leave voice chat** stops microphone capture;
**Mute microphone** keeps you in the room but disables outgoing audio.

Keep the page open, the phone unlocked, and the computer awake. Use HTTPS
(or localhost for development). Browser autoplay restrictions require a click
to enable sound; background tabs and locked phones may suspend alerts or calls.
Use headphones to prevent feedback.

Voice uses WebRTC and PeerJS 1.5.5, loaded from jsDelivr, with PeerJS's public
signaling service. No account or API key is required. A connected visitor
coordinates room presence; the remaining visitors reconnect if that visitor
leaves. All visitors on the hostname can join: this is not a private or
authenticated room. Signaling providers receive connection metadata.
There is no configured TURN relay, so restrictive networks may block audio
even when presence works. Verify a two-device call on your actual networks
before relying on it, and keep another contact method available.

This temporary version lives on `temp/call-emergency`, whose Pages workflow
deploys that branch, not `main`. To restore the regular game, deploy the
unchanged `main` branch using its **Deploy GitHub Pages** workflow and restore
the Pages source branch to `main`. Do not merge this temporary branch.

## Notes

- This project is a client-side game with no backend, no API keys, and no
  credentials checked into source control.
- The README intentionally avoids hosting or deployment specifics because those
  details are environment-sensitive and do not help a reviewer run the game.
- If you want to publish the build, host the generated static files through a
  standard static-site provider or your own CDN; that setup can remain outside
  the public repo to keep the project clean and low-risk for sharing.
