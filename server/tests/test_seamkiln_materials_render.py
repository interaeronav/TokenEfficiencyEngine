"""`sk_materials` carries the card's render properties (A65 P3.3).

`texture` is the one string on a card; every other change is a number. The
derive action used to cast every change to float, which would have refused
the field the render side most wants.
"""

from __future__ import annotations

import pytest

from tee.adapters.seamkiln import SeamkilnAdapter
from tee.app import TeeApp

seamkiln = pytest.importorskip("seamkiln", reason="seamkiln is an optional extra")


def test_derive_accepts_a_texture_and_lists_it(tmp_path) -> None:
    app = TeeApp({"seamkiln": SeamkilnAdapter(tmp_path)}, project_root=tmp_path)
    try:
        card = app.registry.call(
            "sk_materials",
            {
                "action": "derive",
                "base": "cotton_poplin",
                "name": "poplin_glossy",
                "changes": {"roughness": 0.2, "texture": "poplin.png"},
            },
        )
        assert card["render"]["roughness"] == 0.2
        assert card["render"]["texture"] == "poplin.png"
        assert card["render"]["physical"] is False
        assert card["tier"] == "plausible"  # the base is plausible; unchanged by a render edit

        rows = app.registry.call("sk_materials", {"action": "list", "category": "custom"})
        mine = next(r for r in rows["materials"] if r["name"] == "poplin_glossy")
        assert mine["texture"] == "poplin.png" and mine["roughness"] == 0.2

        side = app.registry.call(
            "sk_materials", {"action": "compare", "names": ["cotton_poplin", "poplin_glossy"]}
        )
        assert side["rows"]["roughness"] == [0.5, 0.2]
    finally:
        app.shutdown()
