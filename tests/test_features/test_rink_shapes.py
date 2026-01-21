import numpy as np
import matplotlib.patches as mpatches
from matplotlib.path import Path
from mplhockey.features.rink_shapes import (
    RinkCircle,
    FaceoffCircle,
    Posts,
    CreaseNHL,
    IceSurface,
    OuterBoards,
)


def is_patch(obj):
    return isinstance(obj, (mpatches.PathPatch, mpatches.FancyBboxPatch, mpatches.Patch))


def test_rink_circle_type():
    patch = RinkCircle((0, 0), radius=1.0, color="blue")
    assert is_patch(patch)
    assert patch.get_facecolor() is not None


def test_rink_circle_bounds():
    patch = RinkCircle((0, 0), radius=1.0, color="blue")
    verts = patch.get_path().vertices
    x_min, y_min = verts.min(axis=0)
    x_max, y_max = verts.max(axis=0)
    assert np.isclose(x_max - x_min, 2.0, atol=0.1)
    assert np.isclose(y_max - y_min, 2.0, atol=0.1)


def test_faceoff_circle_cutouts_present():
    patch = FaceoffCircle((0, 0), radius=15.0, thickness=1.0, inside_width=5.0, color="red")
    verts = patch.get_path().vertices
    y_values = verts[:, 1]
    # Ensure there's a gap near y = 0 (the horizontal notch)
    assert np.any(np.abs(y_values) < 1.0)


def test_post_symmetry():
    patch = Posts((0, 0), inside_width=6.0, tube_radius=0.5, color="red")
    verts = patch.get_path().vertices
    y_values = verts[:, 1]
    assert np.isclose(np.abs(y_values.max()), np.abs(y_values.min()), atol=1e-6)


def test_crease_position_and_shape():
    patch = CreaseNHL((10, -20), rect_width=8.0, rect_height=4.0, color="blue")
    verts = patch.get_path().vertices

    length = np.max(verts[:, 0]) - np.min(verts[:, 0])
    expected_length = np.sqrt(4.0**2 + (8.0 / 2) ** 2)

    width = np.max(verts[:, 1]) - np.min(verts[:, 1])
    expected_width = 8.0

    assert np.isclose(length, expected_length, rtol=1e-4)
    assert np.isclose(width, expected_width, rtol=1e-4)


def test_ice_surface():
    patch = IceSurface(ice_width=200, ice_height=80, corner_radius=18, color="#202020")
    verts = patch.get_path().vertices

    length = np.max(verts[:, 0]) - np.min(verts[:, 0])
    expected_length = 200

    width = np.max(verts[:, 1]) - np.min(verts[:, 1])
    expected_width = 80

    assert np.isclose(length, expected_length)
    assert np.isclose(width, expected_width)


def test_boards():
    patch = OuterBoards(ice_width=200, ice_height=80, boards_width=10.0, corner_radius=18, color="#202020")
    verts = patch.get_path().vertices

    length = np.max(verts[:, 0]) - np.min(verts[:, 0])
    expected_length = 220

    width = np.max(verts[:, 1]) - np.min(verts[:, 1])
    expected_width = 100

    assert np.isclose(length, expected_length)
    assert np.isclose(width, expected_width)
