from matplotlib.patches import Circle, PathPatch
from mplhockey.geometry.shapes import (
    _pathpatch_to_shapely,
    _shapely_to_pathpatch,
    union,
    difference,
    intersection,
    unary_union,
    scale,
    translate,
    rotate,
    outline,
    outline_path,
    buffer_path,
    mirror,
    FilledCircle,
    OutlineCircle,
    Sector,
    ArcPatch,
    LinePatch,
    RoundedRectangle,
    EdgeStyle,
)
from shapely.geometry import Polygon, LineString, MultiPolygon
from matplotlib.path import Path
import numpy as np
from shapely.affinity import scale as shapely_scale, rotate as shapely_rotate, translate as shapely_translate


def make_circle_patch(center=(0, 0), radius=1.0, **kwargs):
    return FilledCircle(center, radius, **kwargs)  # Circle(center, radius=radius, **kwargs)


def make_triangle_patch():
    vertices = np.array([[0, 0], [1, 0], [0, 1], [0, 0]])
    codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY]
    return PathPatch(Path(vertices, codes), facecolor="none")


def test_mirror_x_reflects_geometry():
    original = make_circle_patch()
    reflected = mirror(original, axis="x")
    geom_reflected = _pathpatch_to_shapely(reflected)
    geom_expected = shapely_scale(_pathpatch_to_shapely(original), xfact=-1.0, yfact=1.0, origin=(0, 0))

    # Use topological difference instead of pointwise equality
    difference_area = geom_reflected.symmetric_difference(geom_expected).area
    assert difference_area < 1e-6


def test_mirror_y_reflects_geometry():
    original = make_circle_patch()
    reflected = mirror(original, axis="y")
    geom_reflected = _pathpatch_to_shapely(reflected)
    geom_expected = shapely_scale(_pathpatch_to_shapely(original), xfact=-1.0, yfact=1.0, origin=(0, 0))

    assert geom_reflected.symmetric_difference(geom_expected).area < 1e-6


def test_mirror_xy_reflects_both_axes():
    original = make_circle_patch()
    reflected = mirror(original, axis="both")
    geom_reflected = _pathpatch_to_shapely(reflected)
    geom_expected = shapely_scale(_pathpatch_to_shapely(original), xfact=-1.0, yfact=-1.0, origin=(0, 0))

    assert geom_reflected.symmetric_difference(geom_expected).area < 1e-6


def test_scale_patch():
    patch = make_triangle_patch()
    result = scale(patch, xfact=2.0, yfact=3.0, origin=(0.0, 0.0))

    geom = _pathpatch_to_shapely(result)
    expected = shapely_scale(Polygon([[0, 0], [1, 0], [0, 1]]), xfact=2.0, yfact=3.0, origin=(0.0, 0.0))

    assert np.allclose(np.array(geom.exterior.coords), np.array(expected.exterior.coords))


def test_rotate_patch():
    patch = make_triangle_patch()
    result = rotate(patch, angle=90, origin=(0.0, 0.0))

    geom = _pathpatch_to_shapely(result)
    expected = shapely_rotate(Polygon([[0, 0], [1, 0], [0, 1]]), angle=90, origin=(0.0, 0.0))

    # Check that all points match after rotation (order may change)
    assert geom.equals_exact(expected, tolerance=1e-8)


def test_mirror_patch_x():
    patch = make_triangle_patch()
    result = scale(patch, xfact=-1.0, yfact=1.0, origin=(0.0, 0.0))

    geom = _pathpatch_to_shapely(result)
    expected = shapely_scale(Polygon([[0, 0], [1, 0], [0, 1]]), xfact=-1.0, yfact=1.0, origin=(0.0, 0.0))

    assert geom.symmetric_difference(expected).area < 1e-6


def test_translate_patch():
    patch = make_triangle_patch()
    dx, dy = (2.0, 3.0)
    result = translate(patch, (dx, dy))

    geom = _pathpatch_to_shapely(result)
    expected = shapely_translate(Polygon([[0, 0], [1, 0], [0, 1]]), xoff=dx, yoff=dy)

    assert np.allclose(geom.exterior.coords, expected.exterior.coords)


def test_union_of_two_circles():
    c1 = make_circle_patch((0, 0), radius=1)
    c2 = make_circle_patch((1, 0), radius=1)

    result = union(c1, c2)
    geom = _pathpatch_to_shapely(result)

    assert isinstance(geom, Polygon)
    assert geom.area > np.pi  # should be greater than one circle’s area


def test_difference_of_two_circles():
    c1 = make_circle_patch((0, 0), radius=1)
    c2 = make_circle_patch((0.5, 0), radius=1)

    result = difference(c1, c2)
    geom = _pathpatch_to_shapely(result)

    assert isinstance(geom, Polygon)
    assert geom.area < np.pi  # should be smaller than one circle


def test_intersection_of_two_circles():
    c1 = make_circle_patch((0, 0), radius=1)
    c2 = make_circle_patch((0.5, 0), radius=1)

    result = intersection(c1, c2)
    geom = _pathpatch_to_shapely(result)

    assert isinstance(geom, Polygon)
    assert geom.area < np.pi  # overlapping region should be smaller than one full circle


def test_unary_union_multiple_circles():
    c1 = make_circle_patch((0, 0), radius=1)
    c2 = make_circle_patch((2, 0), radius=1)
    c3 = make_circle_patch((4, 0), radius=1)

    result = unary_union([c1, c2, c3])
    geom = _pathpatch_to_shapely(result)

    assert isinstance(geom, MultiPolygon)
    assert np.isclose(geom.area, np.pi * 3, rtol=0.01)  # because c1 and c2 overlap slightly


def test_circle_patch_to_shapely_polygon():
    circle = Circle((0, 0), radius=1.0)
    geom = _pathpatch_to_shapely(circle)

    assert isinstance(geom, Polygon)
    assert np.isclose(geom.area, np.pi, rtol=0.05), "Area not close to pi"


def test_line_patch_to_shapely_linestring():
    vertices = np.array([[0, 0], [1, 0], [1, 1]])
    codes = [Path.MOVETO, Path.LINETO, Path.LINETO]
    path = Path(vertices, codes)
    patch = PathPatch(path)

    geom = _pathpatch_to_shapely(patch, steps=50)

    assert isinstance(geom, LineString)
    # Check start and end match
    assert np.allclose(geom.coords[0], vertices[0])
    assert np.allclose(geom.coords[-1], vertices[-1])
    # Check approximate length
    expected_len = np.linalg.norm(vertices[1] - vertices[0]) + np.linalg.norm(vertices[2] - vertices[1])
    assert np.isclose(geom.length, expected_len, rtol=1e-3)


def test_round_trip_circle_conversion():
    circle = Circle((0, 0), radius=1.0, facecolor="red")
    shapely_geom = _pathpatch_to_shapely(circle)
    round_trip = _shapely_to_pathpatch(shapely_geom, template_patch=circle)

    assert isinstance(round_trip, PathPatch)
    assert np.allclose(round_trip.get_facecolor(), circle.get_facecolor()), "Facecolor mismatch"


def test_round_trip_line_conversion():
    vertices = np.array([[0, 0], [1, 1], [2, 0]])
    codes = [Path.MOVETO, Path.LINETO, Path.LINETO]
    path = Path(vertices, codes)
    patch = PathPatch(path, facecolor="none")

    geom = _pathpatch_to_shapely(patch, steps=50)
    round_trip = _shapely_to_pathpatch(geom, template_patch=patch)

    # Get vertices from the round-tripped path
    round_trip_vertices = round_trip.get_path().vertices

    # Check that shape has the same start and end points
    assert np.allclose(round_trip_vertices[0], vertices[0])
    assert np.allclose(round_trip_vertices[-1], vertices[-1])


def test_buffer_path_sides():
    # Define a simple horizontal line path from (0, 0) to (10, 0)
    path = Path([(0, 0), (10, 0)], [Path.MOVETO, Path.LINETO])
    buffer_amount = 1.0

    # Both sides
    patch_both = buffer_path(path, buffer_amount, side="both")
    geom_both = _pathpatch_to_shapely(patch_both)
    assert isinstance(geom_both, Polygon)
    assert len(geom_both.interiors) == 0  # fully filled, no hole

    # Left side only
    patch_left = buffer_path(path, buffer_amount, side="left")
    geom_left = _pathpatch_to_shapely(patch_left)
    assert isinstance(geom_left, Polygon)
    assert len(geom_left.interiors) == 0, "Expected no holes, but check shape visually"

    # Right side only (negative buffer)
    patch_right = buffer_path(path, buffer_amount, side="right")
    geom_right = _pathpatch_to_shapely(patch_right)
    assert isinstance(geom_right, Polygon)
    assert len(geom_right.interiors) == 0, "Expected no holes, but check shape visually"


def test_buffer_path_sides_closed_path():
    # Define a simple horizontal line path from (0, 0) to (10, 0)
    path = Path(
        [(0, 0), (10, 0), (5, 5), (0, 0), (0, 0)], [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY]
    )
    buffer_amount = 1.0

    # Both sides
    patch_both = outline_path(path, buffer_amount, side="center")
    geom_both = _pathpatch_to_shapely(patch_both)
    assert isinstance(geom_both, Polygon)
    assert len(geom_both.interiors) == 1  # fully filled, no hole

    # Left side only
    patch_left = outline_path(path, buffer_amount, side="outside")
    geom_left = _pathpatch_to_shapely(patch_left)
    assert isinstance(geom_left, Polygon)
    assert len(geom_left.interiors) == 1, "Expected no holes, but check shape visually"

    # Right side only (negative buffer)
    patch_right = outline_path(path, buffer_amount, side="inside")
    geom_right = _pathpatch_to_shapely(patch_right)
    assert isinstance(geom_right, Polygon)
    assert len(geom_right.interiors) == 1, "Expected no holes, but check shape visually"


def test_buffer_patch_sides():
    # Define a simple horizontal line path from (0, 0) to (10, 0)
    patch = RoundedRectangle((0.0, 0.0), width=20.0, height=10.0, corner_radius=0.5, color="#000000")
    buffer_amount = 1.0

    # Both sides
    outline_both = outline(patch, width=buffer_amount, side="center")
    geom_both = _pathpatch_to_shapely(outline_both)
    assert isinstance(geom_both, Polygon)
    assert len(geom_both.interiors) == 1  # fully filled, no hole

    # Left side only
    patch_left = outline(patch, width=buffer_amount, side="outside")
    geom_left = _pathpatch_to_shapely(patch_left)
    assert isinstance(geom_left, Polygon)
    assert len(geom_left.interiors) == 1, "Expected one hole, but check shape visually"

    # Right side only (negative buffer)
    patch_right = outline(patch, width=buffer_amount, side="inside")
    geom_right = _pathpatch_to_shapely(patch_right)
    assert isinstance(geom_right, Polygon)
    assert len(geom_right.interiors) == 1, "Expected one hole, but check shape visually"
