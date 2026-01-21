import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.transforms import Affine2D

from mplhockey.geometry.shapes import FilledCircle, RectanglePatch
from mplhockey.features.feature import parse_features, Feature


# Dummy geometry map for testing — replace with real one if needed
map_features = {
    "circle": FilledCircle,
    "box": RectanglePatch,
}


def test_feature_copy():
    circle = FilledCircle((0, 0), 1.0, "red")
    f1 = Feature("test", circle)
    f2 = f1.copy()
    assert f1.name == f2.name
    assert f1 is not f2
    assert f1.geom is not f2.geom


def test_feature_apply_transform():
    f = Feature("transform", FilledCircle((1, 1), 1.0, "blue"))
    original_transform = f.geom.get_transform()
    transform = Affine2D().translate(10, 0)
    f.apply_transform(transform)
    new_transform = f.geom.get_transform()
    assert new_transform != original_transform


def test_feature_deform_identity():
    f = Feature("deform", FilledCircle((0, 0), 1.0, "black"))
    deformed = f.deform(lambda v: v)  # Identity function
    assert isinstance(deformed, PathPatch)
    assert np.allclose(deformed.get_path().vertices, f.geom.get_path().vertices)


def test_feature_draw():
    fig, ax = plt.subplots()
    f = Feature("draw", FilledCircle((0, 0), 1.0, "blue"))
    f.draw(ax)
    assert any(isinstance(p, PathPatch) for p in ax.patches)


def test_parse_features_basic():
    features = [
        {
            "geometry": "RinkCircle",
            "name": "center_dot",
            "position": (0, 0),
            "radius": 1.0,
            "color": "blue",
        },
        {
            "geometry": "VLine",
            "name": "blue_line",
            "x_pos": 25.0,
            "linewidth": 1.0,
            "color": "blue",
        },
    ]

    parsed = parse_features(features)
    assert len(parsed) == 2
    assert all(isinstance(f, Feature) for f in parsed)
    assert parsed[0].name == "center_dot"
    assert parsed[1].name == "blue_line"


def test_parse_features_invalid_geometry(monkeypatch):
    monkeypatch.setitem(__import__("builtins").__dict__, "map_features", map_features)

    features = [
        {"geometry": "unknown_type", "name": "fail"},
        {"geometry": None, "name": "also_fail"},
    ]
    parsed = parse_features(features)
    assert parsed == []


def test_parse_features_mirroring(monkeypatch):

    features = [
        {
            "geometry": "RinkCircle",
            "name": "mirrored",
            "position": (0, 0),
            "radius": 1.0,
            "color": "black",
            "mirror": "both",
        }
    ]
    parsed = parse_features(features)
    assert parsed[0].name == "mirrored"
