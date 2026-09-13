"""Explicit Fusion measurements use precise geometry, once per measured body."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fixtures_fusion import (
    BoundingBox3D,
    BRepBody,
    CalculationAccuracy,
    Component,
    FakeFusionWire,
    Occurrence,
    PhysicalProperties,
    Point3D,
)

from tee.adapters.fusion import codegen
from tee.adapters.fusion.adapter import FusionAdapter


def bounds(lo: tuple[float, ...], hi: tuple[float, ...]) -> BoundingBox3D:
    box = BoundingBox3D([0, 0, 0])
    box.minPoint, box.maxPoint = Point3D(*lo), Point3D(*hi)
    return box


def properties(
    volume: float, area: float, mass: float, centre: tuple[float, ...]
) -> PhysicalProperties:
    result = PhysicalProperties(volume, area, Point3D(*centre))
    result.mass = mass
    return result


def adapter_with_part(*, component: bool = False) -> FusionAdapter:
    adapter = FusionAdapter(FakeFusionWire())
    adapter.execute(
        [
            {
                "op": "create",
                "kind": "sketch",
                "name": "footprint",
                "as": "footprint",
                "props": {"rects": [[0, 0, 40, 20]]},
            },
            {
                "op": "create",
                "kind": "extrude",
                "name": "part",
                "props": {
                    "sketch": "@footprint",
                    "distance": 10,
                    "operation": "new_component" if component else "new_body",
                },
            },
        ]
    )
    return adapter


@pytest.mark.parametrize("target", [None, "b1"])
def test_root_and_body_use_requested_precision_instead_of_default_properties_and_bounds(
    target: str | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter = adapter_with_part()
    cls = Component if target is None else BRepBody
    wanted = properties(12.345678, 25.01234, 0.0314159, (-4.2, 5.5, 6.25))
    tight = bounds((-5, 4, 6), (-3, 7, 6.8))
    calls: list[int] = []
    box_calls: list[object] = []

    def get_properties(self: object, accuracy: int) -> PhysicalProperties:
        calls.append(accuracy)
        return wanted

    def precise_box(self: object) -> BoundingBox3D:
        box_calls.append(self)
        return tight

    # Explicitly disagree with the precise answers. A fallback would silently
    # return plausible values, which this test must reject.
    monkeypatch.setattr(
        cls, "physicalProperties", property(lambda self: properties(90, 80, 70, (6, 5, 4)))
    )
    monkeypatch.setattr(cls, "boundingBox", property(lambda self: bounds((0, 0, 0), (9, 9, 9))))
    monkeypatch.setattr(cls, "getPhysicalProperties", get_properties)
    monkeypatch.setattr(cls, "preciseBoundingBox", property(precise_box))

    result = adapter.run(codegen.measure_program(target))
    assert result == {
        "volume_mm3": 12345.678,
        "area_mm2": 2501.234,
        "mass_kg": 0.031416,
        "centre_of_mass_mm": [-42, 55, 62.5],
        "bbox_mm": [20, 30, 8],
        "of": target or "root",
    }
    assert calls == [CalculationAccuracy.VeryHighCalculationAccuracy]
    assert len(box_calls) == 1


class WorldBody:
    """A body proxy with distinct world coordinates and deliberately loose defaults."""

    def __init__(self, physical: PhysicalProperties, box: BoundingBox3D) -> None:
        self._physical, self._box = physical, box
        self.physical_calls: list[int] = []
        self.box_calls = 0

    @property
    def physicalProperties(self) -> PhysicalProperties:
        return properties(900, 800, 700, (0, 0, 0))

    @property
    def boundingBox(self) -> BoundingBox3D:
        return bounds((-100, -100, -100), (100, 100, 100))

    def getPhysicalProperties(self, accuracy: int) -> PhysicalProperties:
        self.physical_calls.append(accuracy)
        return self._physical

    @property
    def preciseBoundingBox(self) -> BoundingBox3D:
        self.box_calls += 1
        return self._box


def test_occurrence_measures_each_world_proxy_once_and_unions_precise_bounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = adapter_with_part(component=True)
    bodies = [
        WorldBody(properties(1, 3, 2, (10, -4, 1)), bounds((9, -5, 0), (11, -3, 2))),
        WorldBody(properties(2, 4, 6, (14, 2, 3)), bounds((12, 1, 2), (16, 3, 4))),
    ]
    monkeypatch.setattr(
        Occurrence,
        "bRepBodies",
        property(lambda self: SimpleNamespace(count=len(bodies), item=bodies.__getitem__)),
    )

    def native_properties(*args: object) -> PhysicalProperties:
        pytest.fail("an occurrence measurement used native component coordinates")

    monkeypatch.setattr(Component, "getPhysicalProperties", native_properties)
    result = adapter.run(codegen.measure_program("c1"))
    assert result == {
        "volume_mm3": 3000,
        "area_mm2": 700,
        "mass_kg": 8,
        "centre_of_mass_mm": [130, 5, 25],
        "bbox_mm": [70, 80, 40],
        "bodies": 2,
        "of": "c1",
    }
    for body in bodies:
        assert body.physical_calls == [CalculationAccuracy.VeryHighCalculationAccuracy]
        assert body.box_calls == 1
