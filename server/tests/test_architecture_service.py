"""Persistence, concurrency and path boundaries of the actual architectural service."""

import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from tee.architecture.model import ArchitectureError, Document
from tee.architecture.service import ArchitectureService


def test_preset_survives_reopen_edit_and_persistent_undo(tmp_path):
    service = ArchitectureService(tmp_path)
    created = service.create("A measured example", "compact-house")
    model_id = created["model_id"]
    initial = service.state(model_id)
    assert initial["units"] == "mm" and len(initial["entities"]) == 15
    reopened = ArchitectureService(tmp_path)
    result = reopened.edit(
        model_id, [{"op": "update", "id": "cabinet", "changes": {"width": 1200}}], 1
    )
    assert result["revision"] == 2
    assert reopened.query(model_id, "cabinet")["entity"]["width"] == 1200
    undone = ArchitectureService(tmp_path).undo(model_id, 2)
    assert undone["revision"] == 3
    final = service.state(model_id)
    assert final["entities"] == initial["entities"]
    assert "history" not in final and "history" not in service.status()


def test_read_operations_do_not_create_state(tmp_path):
    service = ArchitectureService(tmp_path)
    assert service.status()["models"] == []
    with pytest.raises(ArchitectureError):
        service.state("building_" + "0" * 16)
    assert not (tmp_path / ".tee").exists()


def test_headless_cabinet_schedule_and_nesting_follow_current_revision(tmp_path):
    service = ArchitectureService(tmp_path)
    model = service.create("Shop fixture", "compact-house")["model_id"]
    result = service.query(
        model,
        "cabinet",
        "cabinet",
        {
            "sheet_width": 1220,
            "sheet_height": 2440,
            "kerf": 3.2,
        },
    )
    assert result["revision"] == 1
    assert result["schedule"] and result["nesting"]["sheets"]
    with pytest.raises(ArchitectureError):
        service.query(model, "south", "cabinet")
    with pytest.raises(ArchitectureError):
        service.query(model, "cabinet", "cabinet", {"sheet_width": 1220})


def test_candidate_promotion_rejects_out_of_project_retained_source(tmp_path, monkeypatch):
    service = ArchitectureService(tmp_path)
    model = service.create("Boundary fixture", "compact-house")["model_id"]
    monkeypatch.setattr(
        service,
        "candidates",
        lambda *args: {
            "proposal": {
                "candidates": [
                    {
                        "id": "candidate",
                        "provenance": {"source_path": str(tmp_path.parent / "other.xyz")},
                    }
                ]
            }
        },
    )
    with pytest.raises(ArchitectureError, match="outside"):
        service.promote(model, "import", "candidate", "ground", {}, 1)
    assert service.state(model)["revision"] == 1


def test_unsupported_join_edit_refuses_before_core_or_persistence_commit(tmp_path):
    service = ArchitectureService(tmp_path)
    mid = service.create("Joined fixture", "compact-house")["model_id"]
    before = service.state(mid)
    operation = {"op": "update", "id": "partition", "changes": {"height": 2700}}
    document = Document.from_dict(before)
    with pytest.raises(ArchitectureError, match="base/top"):
        document.apply([operation], expected_revision=1)
    assert document.revision == 1 and document.entities == before["entities"]
    with pytest.raises(ArchitectureError, match="base/top"):
        service.edit(mid, [operation], 1)
    assert service.state(mid) == before
    checked = service.check(mid)
    assert checked["geometry"]["wall_joins"]["count"] == 6
    assert checked["geometry"]["wall_junctions"]["status"] == "no_wall_overlap_found"
    assert checked["geometry"]["status"] == "not_verified"  # named checks are partial


def test_two_independent_clients_cannot_lose_an_edit(tmp_path):
    services = [ArchitectureService(tmp_path), ArchitectureService(tmp_path)]
    model_id = services[0].create("Concurrent fixture", "compact-house")["model_id"]
    barrier = threading.Barrier(2)

    def edit(index):
        barrier.wait()
        try:
            return services[index].edit(
                model_id,
                [{"op": "update", "id": "cabinet", "changes": {"width": 1000 + index * 100}}],
                1,
            )
        except ArchitectureError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(edit, range(2)))
    assert sum(isinstance(result, ArchitectureError) for result in results) == 1
    assert services[0].state(model_id)["revision"] == 2
    assert services[0].query(model_id, "cabinet")["entity"]["width"] in (1000, 1100)


def test_failed_atomic_replace_preserves_previous_document(tmp_path, monkeypatch):
    service = ArchitectureService(tmp_path)
    model_id = service.create("Failure fixture", "compact-house")["model_id"]
    before = service.state(model_id)

    def fail(*args):
        raise OSError("owned injected replace failure")

    monkeypatch.setattr("tee.architecture.service.os.replace", fail)
    with pytest.raises(OSError, match="injected"):
        service.edit(model_id, [{"op": "update", "id": "cabinet", "changes": {"width": 1100}}], 1)
    assert service.state(model_id) == before
    assert not list((service.root / model_id).glob("*.tmp"))


@pytest.mark.parametrize("path", ["../secret.txt", "/etc/passwd", "a/../../b", "a\\b", "a\x00b"])
def test_import_paths_must_stay_in_project(tmp_path, path):
    with pytest.raises(ArchitectureError):
        ArchitectureService(tmp_path).input_path(path)


def test_links_are_not_authoritative_inputs_or_model_state(tmp_path):
    service = ArchitectureService(tmp_path)
    source = tmp_path / "source.xyz"
    source.write_text("0 0 0\n")
    alias = tmp_path / "alias.xyz"
    alias.symlink_to(source)
    with pytest.raises(ArchitectureError):
        service.input_path("alias.xyz")
    alias.unlink()
    alias.hardlink_to(source)
    with pytest.raises(ArchitectureError):
        service.input_path("source.xyz")
    state_target = tmp_path / "elsewhere"
    state_target.mkdir()
    (tmp_path / ".tee").mkdir()
    service.root.symlink_to(state_target, target_is_directory=True)
    with pytest.raises(ArchitectureError):
        service.create("Must refuse")
    assert not list(state_target.iterdir())


def test_invalid_edit_never_changes_persisted_state(tmp_path):
    service = ArchitectureService(tmp_path)
    model_id = service.create("Validation fixture", "compact-house")["model_id"]
    before = service.state(model_id)
    with pytest.raises(ArchitectureError):
        service.edit(model_id, [{"op": "delete", "id": "south"}], 1)
    assert service.state(model_id) == before


def test_model_index_reports_a_broken_model_without_hiding_others(tmp_path):
    service = ArchitectureService(tmp_path)
    first = service.create("Good model")["model_id"]
    second = service.create("Broken model")["model_id"]
    (service.root / second / "document.json").write_text("not JSON")
    rows = {row["model_id"]: row for row in service.status()["models"]}
    assert rows[first]["project"]["name"] == "Good model"
    assert rows[second]["error"]


def test_new_output_paths_are_unique_and_do_not_overwrite(tmp_path):
    service = ArchitectureService(tmp_path)
    model_id = service.create("JSON export")["model_id"]
    first = service.export(model_id, "json")
    second = service.export(model_id, "json")
    assert first["directory"] != second["directory"]
    assert Path(first["directory"], "document.json").is_file()
    assert Path(second["directory"], "document.json").is_file()
