import json

from voxkiln.cli import main


def test_doctor_runs_anywhere(capsys):
    assert main(["doctor"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["upstream_commit"].startswith("75fbf01")
    assert payload["vendor_tree"] is True
    assert "probe" in payload


def test_gen_without_backend_refuses_structurally(capsys, tmp_path):
    import numpy as np
    from PIL import Image

    img = tmp_path / "in.png"
    Image.fromarray(np.zeros((8, 8, 3), dtype=np.uint8)).save(img)
    code = main(["gen", str(img), "--out", str(tmp_path / "out")])
    payload = json.loads(capsys.readouterr().out)
    # this container has no MPS/CUDA: exit 1 + the exact fix, no traceback
    assert code == 1
    assert payload["error"] == "no_backend"
    assert "voxkiln[model]" in payload["fix"] or "Apple Silicon" in payload["fix"]
