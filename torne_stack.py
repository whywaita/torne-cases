# /// script
# requires-python = ">=3.11"
# dependencies = ["manifold3d>=3.0", "numpy"]
# ///
"""Sony torne (CECH-ZD1J) を積み重ねて固定するラック (Raspberry Pi クラスタケース風) の STL 生成スクリプト。

構成:
  - tray   : torne を 1 台載せる棚板。torne の台数 + 0 枚 (一番下も tray)
  - lid    : 最上段のフタ (ガイドなし)
  - spacer : 棚板の間に挟む柱。M3 全ネジ / 長ネジを通す。既製の M3 スタンドオフを使うなら不要

座標系: X = torne の幅 (前面), Y = 奥行き (-Y が前面, +Y が背面のケーブル側), Z = 高さ。
"""

import struct
import sys
from pathlib import Path

import numpy as np
from manifold3d import CrossSection, JoinType, Manifold, OpType

# --- torne 本体 (実測: 幅99 x 高さ24 x 奥行き99 mm) ---
# 取扱説明書の 100 x 24 x 112 mm は突起部込み。背面中央は開けてあるので突起はそこに逃がす
TORNE_W = 99.0
TORNE_D = 99.0
TORNE_H = 24.0

# --- 棚板 ---
CLEARANCE = 1.0  # torne とガイドの片側すき間
POCKET_W = TORNE_W + 2 * CLEARANCE
POCKET_D = TORNE_D + 2 * CLEARANCE
PLATE_T = 3.0
RAIL_T = 2.4  # ガイドの厚み (0.4mm ノズルで 6 周)
RAIL_H = 5.0  # 左右ガイドの高さ
RETURN_L = 12.0  # 前後の角ストッパーの長さ
BACK_STOP_H = RAIL_H  # 背面側ストッパー (奥に押し込みすぎ防止)
FRONT_STOP_H = 2.0  # 前面側ストッパー (持ち上げて抜ける低さ)
CORNER_R = 6.0

# --- 柱 ---
HOLE_D = 3.4  # M3 用通し穴
STANDOFF_CLEAR_R = 3.5  # 柱 (印刷スペーサー OD7 / 六角スタンドオフ 5.5 対辺) が占める半径
HOLE_X = POCKET_W / 2 + RAIL_T + STANDOFF_CLEAR_R + 0.6
HOLE_Y = POCKET_D / 2 + RAIL_T + STANDOFF_CLEAR_R + 0.6
EDGE = 6.0  # 穴中心から板の端まで
PLATE_W = 2 * (HOLE_X + EDGE)
PLATE_D = 2 * (HOLE_Y + EDGE)

# 棚板同士の内のり = スペーサー長。既製スタンドオフ (オス-メス) を使う場合はその長さに合わせる
GAP = 30.0
SPACER_OD = 7.0

# --- 通気スリット ---
VENT_N = 7
VENT_W = 6.0
VENT_PITCH = 12.0
VENT_L = 84.0

SEGMENTS = 48


def rounded_rect(w, d, r):
    return CrossSection.square((w - 2 * r, d - 2 * r), center=True).offset(r, JoinType.Round, 2.0, SEGMENTS)


def plate_outline():
    return rounded_rect(PLATE_W, PLATE_D, CORNER_R)


def holes(height):
    cyl = Manifold.cylinder(height + 2, HOLE_D / 2, HOLE_D / 2, SEGMENTS).translate((0, 0, -1))
    return Manifold.batch_boolean(
        [cyl.translate((sx * HOLE_X, sy * HOLE_Y, 0)) for sx in (-1, 1) for sy in (-1, 1)],
        OpType.Add,
    )


def vent_slots(height):
    slot = rounded_rect(VENT_W, VENT_L, VENT_W / 2 - 0.01).extrude(height + 2).translate((0, 0, -1))
    x0 = -(VENT_N - 1) * VENT_PITCH / 2
    return Manifold.batch_boolean(
        [slot.translate((x0 + i * VENT_PITCH, 0, 0)) for i in range(VENT_N)], OpType.Add
    )


def lid(vents=True):
    m = plate_outline().extrude(PLATE_T) - holes(PLATE_T)
    if vents:
        m = m - vent_slots(PLATE_T)
    return m


def _box(x0, x1, y0, y1, h):
    return Manifold.cube((x1 - x0, y1 - y0, h)).translate((x0, y0, PLATE_T))


def guides():
    hw, hd, t = POCKET_W / 2, POCKET_D / 2, RAIL_T
    parts = []
    for s in (-1, 1):
        # 左右ガイド (全長)
        x0, x1 = (hw, hw + t) if s > 0 else (-hw - t, -hw)
        parts.append(_box(x0, x1, -hd - t, hd + t, RAIL_H))
        # 背面ストッパー (角のみ。中央はケーブル用に開ける)
        rx0, rx1 = (hw - RETURN_L, hw) if s > 0 else (-hw, -hw + RETURN_L)
        parts.append(_box(rx0, rx1, hd, hd + t, BACK_STOP_H))
        # 前面ストッパー (低い。持ち上げて引き出す)
        parts.append(_box(rx0, rx1, -hd - t, -hd, FRONT_STOP_H))
    return Manifold.batch_boolean(parts, OpType.Add)


def tray():
    return lid() + guides()


def spacer():
    outer = Manifold.cylinder(GAP, SPACER_OD / 2, SPACER_OD / 2, SEGMENTS)
    inner = Manifold.cylinder(GAP + 2, HOLE_D / 2, HOLE_D / 2, SEGMENTS).translate((0, 0, -1))
    return outer - inner


PARTS = {"tray": tray, "lid": lid, "spacer": spacer}


def write_stl(m, path):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties, dtype=np.float32)[:, :3]
    tri = np.asarray(mesh.tri_verts, dtype=np.int64)
    a, b, c = v[tri[:, 0]], v[tri[:, 1]], v[tri[:, 2]]
    n = np.cross(b - a, c - a)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    rec = np.zeros(
        len(tri),
        dtype=[("n", "<f4", 3), ("a", "<f4", 3), ("b", "<f4", 3), ("c", "<f4", 3), ("attr", "<u2")],
    )
    rec["n"], rec["a"], rec["b"], rec["c"] = n, a, b, c
    with open(path, "wb") as f:
        f.write(b"torne-stack".ljust(80, b"\0"))
        f.write(struct.pack("<I", len(tri)))
        f.write(rec.tobytes())


def main(out_dir="stl"):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in PARTS.items():
        write_stl(fn(), out / f"{name}.stl")
    print(f"plate {PLATE_W:.1f} x {PLATE_D:.1f} x {PLATE_T} mm, gap {GAP} mm, pitch {GAP + PLATE_T} mm")
    print(f"holes at ±{HOLE_X:.1f}, ±{HOLE_Y:.1f} ({2 * HOLE_X:.1f} x {2 * HOLE_Y:.1f} mm pitch)")


if __name__ == "__main__":
    main(*sys.argv[1:])
