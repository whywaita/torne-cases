import struct

import pytest

import torne_stack as ts

A1_MINI_BED = 180.0


def bbox_size(m):
    b = m.bounding_box()
    return (b[3] - b[0], b[4] - b[1], b[5] - b[2])


@pytest.mark.parametrize("name", ["tray", "lid", "spacer"])
def test_parts_are_valid_solids(name):
    m = ts.PARTS[name]()
    assert not m.is_empty()
    assert m.volume() > 0
    assert m.genus() >= 0


@pytest.mark.parametrize("name", ["tray", "lid", "spacer"])
def test_parts_fit_a1_mini(name):
    sx, sy, sz = bbox_size(ts.PARTS[name]())
    assert sx <= A1_MINI_BED
    assert sy <= A1_MINI_BED
    assert sz <= A1_MINI_BED


def test_pocket_has_half_mm_clearance_per_side():
    # 実測 99 x 99 mm + 片側 0.5mm
    assert ts.POCKET_W == pytest.approx(100.0)
    assert ts.POCKET_D == pytest.approx(100.0)


def test_torne_footprint_does_not_overlap_guides():
    from manifold3d import Manifold

    torne = Manifold.cube((ts.TORNE_W, ts.TORNE_D, ts.TORNE_H), True).translate(
        (0, 0, ts.PLATE_T + ts.TORNE_H / 2)
    )
    assert (ts.guides() ^ torne).volume() == pytest.approx(0.0, abs=1e-6)


def test_gap_allows_lifting_torne_over_front_stop():
    # torne を前方ストッパーの上に持ち上げて抜き差しできること
    assert ts.GAP >= ts.TORNE_H + ts.FRONT_STOP_H + 1.0


def _standoffs():
    from manifold3d import Manifold, OpType

    r = ts.STANDOFF_CLEAR_R
    cyl = Manifold.cylinder(ts.GAP, r, r, 48).translate((0, 0, ts.PLATE_T))
    return Manifold.batch_boolean(
        [cyl.translate((sx * ts.HOLE_X, sy * ts.HOLE_Y, 0)) for sx in (-1, 1) for sy in (-1, 1)],
        OpType.Add,
    )


def test_standoffs_do_not_hit_guides():
    assert (ts.guides() ^ _standoffs()).volume() == pytest.approx(0.0, abs=1e-6)


def test_torne_slides_out_between_front_standoffs():
    # 前面の柱の間を torne が通り抜けられること
    assert ts.HOLE_X - ts.STANDOFF_CLEAR_R >= ts.POCKET_W / 2


def test_tray_is_compact():
    assert ts.PLATE_W <= 120.0
    assert ts.PLATE_D <= 120.0


def test_holes_keep_edge_margin():
    assert ts.PLATE_W / 2 - ts.HOLE_X - ts.HOLE_D / 2 >= 3.0
    assert ts.PLATE_D / 2 - ts.HOLE_Y - ts.HOLE_D / 2 >= 3.0


def test_tray_has_four_holes():
    # 穴の分だけ板の体積が減っていること
    solid = ts.plate_outline().extrude(ts.PLATE_T)
    holes = 4 * 3.14159 * (ts.HOLE_D / 2) ** 2 * ts.PLATE_T
    assert ts.lid(vents=False).volume() == pytest.approx(solid.volume() - holes, rel=0.02)


def test_spacer_length_matches_gap():
    assert bbox_size(ts.spacer())[2] == pytest.approx(ts.GAP)


def test_write_stl(tmp_path):
    p = tmp_path / "spacer.stl"
    ts.write_stl(ts.spacer(), p)
    data = p.read_bytes()
    (n,) = struct.unpack("<I", data[80:84])
    assert n > 0
    assert len(data) == 84 + 50 * n
