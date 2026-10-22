# torne-cases

English | [日本語](README.ja.md)

A stacking rack for Sony torne (CECH-ZD1J, measured 99 x 99 x 24 mm), styled after Raspberry Pi cluster cases.
Every part fits on a Bambu Lab A1 mini (180 x 180 x 180 mm) build plate.

![preview](docs/preview.png)

![Three torne units stacked in the rack](docs/photo.jpg)

## Parts

| File | Quantity | Description |
| --- | --- | --- |
| `stl/tray.stl` | One per torne | Shelf, 118 x 118 x 3 mm (100 x 100 mm inside the guides, 0.5 mm clearance per side). Side guides, rear stopper (5 mm tall), front stopper (2 mm), and ventilation slots |
| `stl/lid.stl` | 1 | Top lid |
| `stl/spacer.stl` | 4 x number of units | Pillar (OD 7 / ID 3.4 / length 30 mm). Not needed if you use off-the-shelf standoffs |

Mounting holes are φ3.4 for M3, on a 108 x 108 mm pitch (the pillars sit just outside the corners of the torne). Shelf pitch is 33 mm (30 mm pillar + 3 mm shelf).
The center of the rear is open, so the antenna and USB cables exit there. To remove a torne, lift it slightly and slide it out the front.

## Assembly

- Off-the-shelf: four M3 male-female 30 mm standoffs per level. Fix the bottom shelf from below with M3 screws
- Printed: sandwich `spacer.stl` between the shelves and tighten with M3 threaded rod (about levels x 33 + 10 mm) or nuts

### Parts I bought and am testing

| Part | Use | Link |
| --- | --- | --- |
| uxcell brass hex standoff M3 x 30 mm + 6 mm male-female, 10 pcs | Pillars between shelves (4 per level) | https://www.amazon.co.jp/dp/B078T9NN35 |
| uxcell M3 x 5 mm pan head Phillips screw, 304 stainless, 20 pcs | Fixing the bottom shelf from below | https://www.amazon.co.jp/dp/B0DZP3P75T |

## Build

```sh
uv run torne_stack.py          # writes to stl/
uv run --with pytest --with manifold3d --with numpy pytest
```

Dimensions can be changed via the constants at the top of `torne_stack.py`. To match the length of the standoffs you have, change `GAP` (27 mm or more).

## Recommended print settings

PETG (safer than PLA because torne gets warm), 0.2 mm layers, 3 walls, 20% infill, no supports.
