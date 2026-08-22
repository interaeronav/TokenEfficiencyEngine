import pytest

from tee.extract.images import (
    budgeted_jpeg,
    contact_sheet,
    dedupe_photos,
    ground_resolution_m_per_px,
    image_tokens,
    size_for_budget,
)


def make_photo(path, seed=0, size=(800, 600)):
    from PIL import Image, ImageDraw

    img = Image.new("RGB", size, (40 + seed * 3, 60, 90))
    draw = ImageDraw.Draw(img)
    draw.ellipse((seed * 5, 50, 300 + seed * 5, 350), fill=(200, 120, 40))
    img.save(path, "JPEG", quality=88)
    return path


def test_token_math_matches_patch_formula():
    assert image_tokens(28, 28) == 1
    assert image_tokens(1568, 1568) == 56 * 56
    w, h = size_for_budget(4000, 3000, 1000)
    assert image_tokens(w, h) <= 1000
    assert max(w, h) <= 1568
    assert w / h == pytest.approx(4 / 3, rel=0.06)


def test_budgeted_jpeg_and_region(tmp_path):
    photo = make_photo(tmp_path / "p.jpg")
    data, info = budgeted_jpeg(photo, 300)
    assert data[:2] == b"\xff\xd8"
    assert info["tokens"] <= 300
    _crop, crop_info = budgeted_jpeg(photo, 300, region=[0, 0, 200, 200])
    assert crop_info["width"] <= 200 * 3  # upscale never explodes cost
    assert crop_info["tokens"] <= 300


def test_dedupe_groups_near_duplicates(tmp_path):
    import imagehash
    from PIL import Image

    entries = []
    for i, seed in enumerate((0, 1, 40)):  # 0 and 1 near-identical, 40 distinct
        path = make_photo(tmp_path / f"p{i}.jpg", seed=seed)
        with Image.open(path) as img:
            entries.append({"hash": f"hash{i}" + "0" * 58, "phash": str(imagehash.phash(img))})
    groups = dedupe_photos(entries)
    assert len(groups) == 2
    first = groups[0]
    assert first["duplicates"] or first["similar"]


def test_contact_sheet_bounded(tmp_path):
    entries = [
        {"path": make_photo(tmp_path / f"c{i}.jpg", seed=i * 7), "label": f"img{i}"}
        for i in range(6)
    ]
    sheet = contact_sheet(entries, tmp_path / "sheet.jpg")
    assert sheet["tokens"] <= 4784
    assert len(sheet["cells"]) == 6
    assert (tmp_path / "sheet.jpg").exists()


def test_ground_resolution():
    # equator, zoom 19: ~0.30 m/px (research 12)
    assert ground_resolution_m_per_px(0.0, 19) == pytest.approx(0.298, abs=0.01)
    assert ground_resolution_m_per_px(60.0, 19) < 0.2  # cos(lat) shrinks it


def test_gps_parser_units():
    from tee.extract.images import _parse_gps

    gps = {1: "S", 2: (22.0, 34.0, 12.0), 3: "E", 4: (17.0, 4.0, 58.8), 6: 1720.0}
    lat, lon, alt = _parse_gps(gps)
    assert lat == pytest.approx(-22.57, abs=0.01)
    assert lon == pytest.approx(17.083, abs=0.001)
    assert alt == 1720.0
