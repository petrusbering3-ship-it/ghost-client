# Ghost client guide (Minecraft 26.2, Fabric)

## 1. Install
**Easiest: the installer**
1. Install Python 3.10+ (python.org, tick "Add Python to PATH") and Java 25 (adoptium.net).
2. Double-click `ghost_installer.py`. A blue stained-glass window opens.
3. Press **Fabric** (installs Fabric Loader for 26.2), then **INSTALL** (copies the mod and downloads Fabric API).
4. Start Minecraft with the **Fabric** profile.
- Want a real `.exe`? Double-click `build_exe.bat` on Windows. It makes `dist\GhostInstaller.exe` with the mod inside.
- Buttons: Browse/Detect (find .minecraft), Remove (uninstall), Folder (open mods folder).

**Manual:** put `ghost-26.2.jar` and Fabric API 0.161.0+26.2 in `.minecraft/mods` (needs Fabric Loader 0.20.1+).

## 2. The menu (Right Shift)
A see-through blue stained-glass window with a sidebar (Render, World, Market, Client), a search box and module cards.
- **Click** a card = on/off. **Right click** (or the three-line icon) = settings drawer. **Middle click** = bind a key.
- The drawer has sliders, switches, option cyclers and text boxes (the Ore Scanner seed). Everything saves by itself.
- Esc or Right Shift closes. **Hold C** to zoom. `[` and `]` are the Flip Assistant keys.

## 3. Modules
| Panel | Modules |
|---|---|
| Render | Fullbright, Freecam, X-Ray, Custom Sky, Entity ESP, Tracers, Pearl Paths, Zoom |
| World | Ore Scanner, Base Finder, Sound ESP, Anti Vanish, Storage ESP, Chunk Borders, Player Alert, Waypoints |
| Market | Flip Assistant |
| Client | HUD, Theme, Performance |

### Ore Scanner
Predicts hidden ores from the world seed, using the game's own ore rules plus the noise veins. In a real vanilla test world it
predicted about 97% of all ores.
1. Right click the module, type the seed in **Seed** (or `/gscan seed <seed>`). **You need the server's real seed.**
2. Turn it on. Boxes and labels show hidden ores through walls (ore, distance, direction, Y, size).
3. After a few chunks it says "seed check OK: 97%". If it says the seed is wrong, it is wrong (or the server has custom worldgen).
- Every ore has a normal and a **Deepslate** checkbox (coal, iron, copper, gold, redstone, lapis, diamond, emerald).
- Settings: Chunks, Distance, Boxes per ore, Alpha, Boxes, Labels, Labels shown. Overworld only.

### Freecam
Fly the camera: WASD, Space up, Shift down, Sprint faster. Your body stays still and cannot click. It turns off if you take damage.
It only shows chunks the server already sent.

### X-Ray
Only ores and chosen blocks are drawn; everything else is invisible. Toggling rebuilds the world view (give it a second).
On servers with anti-xray it only shows what the server sent, so use the Ore Scanner there.

### Flip Assistant
- Open the auction house (`/ah`) and browse. Underpriced listings get a pulsing outline and "+86%" and a FLIPS panel.
- It learns prices as you browse (saved in `config/ghost_flip_prices.json`). With an API key (`/api` in the server, then
  `/gflip key <key>`) it uses real sales.
- `[` lists the item you hold at the fair price. `]` searches the best flip.
- If it reads 0 listings: open the auction house, run `/gflip dump`, check `config/ghost_flip_dump.txt`.

### Performance
Presets Balanced and Max FPS lower particles, clouds, entity shadows, entity range and optionally render distance.
Your own values come back when you turn it off.

### Others
Custom Sky (presets, stars, fog, time lock), Entity ESP, Tracers, Storage ESP (chests, shulkers, spawners), Pearl Paths
(landing spot of thrown pearls), Chunk Borders, Player Alert, Waypoints, HUD (watermark, module list, coordinates, toasts, low-health
warning), Theme (accent colour).

## 4. Commands
`/gscan seed <seed>|status|reset`
`/gflip key <key>|probe|dump|list|go <n>|sell|config|set <name> <value>`
`/gwp add <name>|list|del <name>`

## 5. Files (in the `config` folder)
`ghost_config.json` (settings, keybinds, theme), `ghost.properties` (seed), `ghost_flip_prices.json`, `ghost_flip.properties`,
`ghost_waypoints.json`, `ghost_bases.txt`.

## 6. If something does not work
- No menu: check the mod is in `mods`, you used the Fabric profile, and Right Shift is not bound elsewhere.
- Freecam or X-Ray odd: other rendering mods (Sodium, Iris, Spectre) can fight over the camera and chunk drawing. Try Ghost alone.
- Send `logs/latest.log` if anything crashes.

## 7. What was verified (real Minecraft 26.2 client, production jar)
Ore scanner 97% match, 16 modules on together without errors, Performance lowers and restores options, Freecam detaches the
camera and leaves the player in place, X-Ray shows ores only, Zoom, config save/load, `/gwp`, auction deals on screen, and the
installer installing into a Minecraft folder. See the `screenshots` folder.
Not tested: DonutSMP's real auction screen and API (the price format may need `/gflip dump`), and the Windows `.exe` build.
