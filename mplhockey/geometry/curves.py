import numpy as np
from matplotlib.path import Path
from math import comb


class BezierCurve:
    """
    Evaluate Bézier curves of arbitrary degree using Bernstein polynomials.

    This class takes a sequence of control points and produces a callable object
    that evaluates the corresponding Bézier curve at any given set of parameter values.

    Parameters
    ----------
    control_points : array-like of shape (n+1, d)
        Control points defining the Bézier curve, where `n` is the degree and `d` is
        the dimensionality (e.g., 2 for 2D curves).

    Attributes
    ----------
    control_points : ndarray
        Array of control points.
    degree : int
        Degree of the Bézier curve (number of control points minus one).

    Examples
    --------
    >>> curve = BezierCurve(np.array([[0, 0], [1, 2], [2, 0]]))  # Quadratic
    >>> points = curve(np.linspace(0, 1, 100))  # Sample 100 points on the curve
    """

    def __init__(self, control_points):
        self.control_points = control_points
        self.degree = len(control_points) - 1

    def __call__(self, t):
        t = np.atleast_1d(t)
        n = self.degree
        points = np.zeros((len(t), self.control_points.shape[1]))
        for k in range(n + 1):
            binomial = comb(n, k)
            term = (binomial * (t**k) * ((1 - t) ** (n - k)))[:, None]
            points += term * self.control_points[k]
        return points if len(points) > 1 else points[0]


def resample_path(path, samples_per_segment=50):
    """
    Resample a Matplotlib Path by linearizing Bézier curves into line segments.

    This function walks through a `Path` and replaces any `CURVE3` (quadratic) or
    `CURVE4` (cubic) Bézier segments with a series of `LINETO` segments, using
    uniform sampling in parameter space. `MOVETO` and `CLOSEPOLY` codes are preserved.

    Parameters
    ----------
    path : matplotlib.path.Path
        The input path to resample.
    samples_per_segment : int, optional
        The number of samples per Bézier segment. Higher values yield smoother approximations.
        Default is 50.

    Returns
    -------
    matplotlib.path.Path
        A new `Path` where all Bézier segments have been replaced with
        linear segments (`LINETO`), while preserving subpath structure.

    Notes
    -----
    - `CURVE3` (quadratic Bézier) segments use 3 points: [P0, P1, P2]
    - `CURVE4` (cubic Bézier) segments use 4 points: [P0, P1, P2, P3]
    - `MOVETO` and `CLOSEPOLY` commands are preserved as-is.
    - Sampling does not include the first control point (to avoid duplication),
      but includes the final point to ensure completeness.

    See Also
    --------
    matplotlib.path.Path : The core path structure used for patches.
    BezierCurve : A callable class for evaluating Bézier curves.
    """
    vertices = path.vertices
    codes = path.codes
    n = len(vertices)

    new_vertices = []
    new_codes = []

    i = 0
    while i < n:
        code = codes[i] if codes is not None else Path.LINETO

        if code == Path.MOVETO:
            # Start of a new subpath
            new_vertices.append(vertices[i])
            new_codes.append(Path.MOVETO)
            i += 1

        elif code == Path.LINETO:
            new_vertices.append(vertices[i])
            new_codes.append(Path.LINETO)
            i += 1

        elif code == Path.CURVE3:
            ctrl_points = vertices[i - 1 : i + 2]
            segment = BezierCurve(ctrl_points)
            s = np.linspace(0, 1, samples_per_segment + 1, endpoint=True)[1:]
            points = segment(s)
            for pt in points:
                new_vertices.append(pt)
                new_codes.append(Path.LINETO)
            i += 2

        elif code == Path.CURVE4:
            ctrl_points = vertices[i - 1 : i + 3]
            segment = BezierCurve(ctrl_points)
            s = np.linspace(0, 1, samples_per_segment + 1, endpoint=True)[1:]
            points = segment(s)
            for pt in points:
                new_vertices.append(pt)
                new_codes.append(Path.LINETO)
            i += 3

        elif code == Path.CLOSEPOLY:
            new_vertices.append(vertices[i])  # Close current subpath
            new_codes.append(Path.CLOSEPOLY)
            i += 1

        else:
            i += 1

    return Path(np.array(new_vertices), new_codes)
