import numpy as np
from matplotlib.path import Path
from mplhockey.geometry.curves import BezierCurve, resample_path


def test_linear_bezier():
    curve = BezierCurve(np.array([[0, 0], [1, 1]]))
    t = np.linspace(0, 1, 5)
    points = curve(t)
    expected = np.array([[ti, ti] for ti in t])
    np.testing.assert_allclose(points, expected, rtol=1e-6)


def test_quadratic_bezier_midpoint():
    curve = BezierCurve(np.array([[0, 0], [1, 2], [2, 0]]))
    midpoint = curve(0.5)
    expected = np.array([1.0, 1.0])
    np.testing.assert_allclose(midpoint, expected, rtol=1e-6)


def test_cubic_bezier_endpoints():
    control_points = np.array([[0, 0], [1, 2], [2, 2], [3, 0]])
    curve = BezierCurve(control_points)
    p0 = curve(0.0)
    p1 = curve(1.0)
    np.testing.assert_allclose(p0, control_points[0], rtol=1e-6)
    np.testing.assert_allclose(p1, control_points[-1], rtol=1e-6)


def test_resample_path_converts_curves():
    from matplotlib.path import Path

    # Define a path with a MOVETO + CURVE4 (cubic Bézier)
    path_data = [
        (Path.MOVETO, [0, 0]),
        (Path.CURVE4, [1, 2]),
        (Path.CURVE4, [2, 2]),
        (Path.CURVE4, [3, 0]),
        (Path.CLOSEPOLY, [0, 0]),
    ]
    codes, verts = zip(*path_data)
    path = Path(verts, codes)

    resampled = resample_path(path, samples_per_segment=10)

    # CURVE4 is replaced with 10 LINETO segments, so all codes should be MOVETO/LINETO/CLOSEPOLY
    assert all(c in (Path.MOVETO, Path.LINETO, Path.CLOSEPOLY) for c in resampled.codes)

    # There should be 10 points from curve + 1 close + 1 moveto = 12
    assert len(resampled.vertices) == 12
