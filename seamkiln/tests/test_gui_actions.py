"""The shell's buttons build Commands - tested with NO Qt (A65 P3.4).

Law 3: a button builds a Command and hands it to the session. The follow-up
verbs were script- and TEE-only for eleven campaigns because nothing checked
the shell on a machine without Qt. The action table is Qt-free on purpose,
so this runs everywhere the core does, and the list of verbs the shell still
lacks a button for is asserted against `VERBS` rather than remembered.
"""

from __future__ import annotations

import pytest

from seamkiln.gui.app import ACTIONS, VERBS_WITHOUT_A_BUTTON, _button, _pull, _walk, _zip
from seamkiln.session import VERBS, Command, Session


def test_the_action_table_and_the_gap_list_account_for_every_verb() -> None:
    session = Session()
    session.apply(Command("block", {"block": "jacket-zip"}))
    covered = set()
    for label, factory in ACTIONS:
        assert isinstance(label, str) and label
        if factory is _pull:
            continue  # needs a garment; covered below
        command = factory(session)
        assert isinstance(command, Command) and command.op in VERBS, label
        covered.add(command.op)
    covered.add("pull")
    assert covered | set(VERBS_WITHOUT_A_BUTTON) == set(VERBS)
    assert not (covered & set(VERBS_WITHOUT_A_BUTTON)), "a verb is listed as both"


def test_a_button_on_a_pattern_without_an_opening_says_so() -> None:
    session = Session()
    session.apply(Command("block", {"block": "tee"}))
    with pytest.raises(ValueError, match="no opening"):
        _zip(session)
    with pytest.raises(ValueError, match="no opening"):
        _button(session)
    with pytest.raises(ValueError, match="no pattern"):
        _zip(Session())


def test_the_follow_up_buttons_run_through_the_session() -> None:
    pytest.importorskip("numba")
    session = Session()
    for command in (
        Command("block", {"block": "jacket-zip"}),
        Command("body", {"kind": "mannequin"}),
        Command("arrange", {"particle_distance_mm": 20.0}),
        Command("drape", {"fabric": "cotton_poplin", "frames": 30}),
    ):
        session.apply(command)

    zipped = _zip(session)
    assert zipped.args["opening"] == "centre-front"
    zipped.args["frames"] = 20
    assert session.apply(zipped)["material"] == "metal"

    button = _button(session)
    assert button.args["panel"] != button.args["hole_panel"]
    button.args["frames"] = 20
    assert session.apply(button)["fastened"] == 1

    walk = _walk(session)
    walk.args.update({"cycles": 0.25, "fps": 4, "samples_per_cycle": 4})
    assert session.apply(walk)["body"] == "mannequin"

    pull = _pull(session)
    pull.args.update({"steps": 3, "settle": 5})
    assert (pull.args["to_x"], pull.args["to_z"]) != (pull.args["x"], pull.args["z"])
    assert "rate" in session.apply(pull)
    assert [c.op for c in session.history][-4:] == ["zip", "button", "walk", "pull"]
