from shapely.geometry import Polygon, LineString, Point, LinearRing, MultiPolygon
from shapely.ops import unary_union as shapely_unary_union
from shapely import affinity
from matplotlib.path import Path
from matplotlib.patches import PathPatch
import numpy as np
from .curves import resample_path
from enum import Enum
from matplotlib import patches
from shapely.geometry.polygon import orient


class EdgeStyle(Enum):
    ROUND = 1  # Rounded corners and caps
    FLAT = 2  # Flat caps (a.k.a. "butt")
    SQUARE = 3  # Square caps or joins


def _pathpatch_to_shapely(patch: PathPatch, steps=50):
    """
    Convert a Matplotlib PathPatch to a Shapely geometry.

    This function transforms a `PathPatch` into a valid Shapely geometry by:
    - Applying the patch's transform.
    - Resampling Bézier curves into linear segments.
    - Splitting compound paths into rings.
    - Interpreting clockwise (CW) rings as solid regions and counter-clockwise (CCW) rings as holes.

    Parameters
    ----------
    patch : matplotlib.patches.PathPatch
        The PathPatch object to convert. Must be a closed path to produce a polygon;
        otherwise, a LineString is returned.
    steps : int, optional
        The number of samples per Bézier segment when resampling the path.
        Higher values produce smoother geometries. Default is 50.

    Returns
    -------
    geometry : shapely.geometry.BaseGeometry
        A Shapely geometry representing the patch. This may be:
        - `Polygon` or `MultiPolygon` if the path is closed.
        - `LineString` if the path is open.
        - A union of shapes if multiple rings are present.

    Notes
    -----
    - Holes are detected via ring orientation: CCW rings are treated as holes.
    - If only CCW rings are present, they are unioned to form a single shape.
    - Uses `shapely.ops.unary_union` for combining rings.
    - The input path is resampled using `resample_path` to linearize curves.

    See Also
    --------
    matplotlib.path.Path
    shapely.geometry.Polygon
    shapely.geometry.LineString
    """
    path = patch.get_path()
    transformed_path = patch.get_transform().transform_path(resample_path(path, samples_per_segment=steps))

    vertices = transformed_path.vertices
    codes = transformed_path.codes

    if codes is None or Path.CLOSEPOLY not in codes:
        return LineString(vertices)

    # Break into subpaths
    subpaths = []
    current = []

    for vert, code in zip(vertices, codes):
        if code == Path.MOVETO:
            if current:
                subpaths.append(np.array(current))
                current = []
            current.append(vert)
        elif code in (Path.LINETO, Path.CLOSEPOLY):
            current.append(vert)
            if code == Path.CLOSEPOLY:
                subpaths.append(np.array(current))
                current = []

    if current:
        subpaths.append(np.array(current))

    # Convert each ring to Polygon, classify as add/subtract
    adds = []
    subtracts = []

    for ring in [LinearRing(p) for p in subpaths if len(p) >= 3]:
        poly = Polygon(ring)
        if ring.is_ccw:
            subtracts.append(poly)
        else:
            adds.append(poly)

    if not adds and not subtracts:
        return LineString(vertices)
    elif not adds:
        # Just holes? Weird, but treat as union of subtracted shapes
        return shapely_unary_union(subtracts)

    # Combine adds first
    result = shapely_unary_union(adds)

    # Subtract holes
    for hole in subtracts:
        result = result.difference(hole)

    return result


def _shapely_to_pathpatch(geom, template_patch: PathPatch = None) -> PathPatch:
    """
    Convert a Shapely geometry into a Matplotlib PathPatch.

    This function translates Shapely geometries (`Polygon`, `MultiPolygon`, or `LineString`)
    into Matplotlib `PathPatch` objects for rendering. It supports compound paths
    and polygon holes. Optional visual properties can be inherited from a template patch.

    Parameters
    ----------
    geom : shapely.geometry.BaseGeometry
        The Shapely geometry to convert. Must be one of:
        - `Polygon`: possibly with interior holes
        - `MultiPolygon`: a collection of polygons
        - `LineString`: an open path
        Other geometry types are not supported.

    template_patch : matplotlib.patches.PathPatch, optional
        If provided, the resulting `PathPatch` will inherit `facecolor` and `edgecolor`
        from this patch. If not provided, default colors are used.

    Returns
    -------
    patch : matplotlib.patches.PathPatch
        A `PathPatch` representing the given geometry, suitable for adding to a Matplotlib axis.

    Raises
    ------
    NotImplementedError
        If the provided geometry type is not supported.

    Notes
    -----
    - For `Polygon` and `MultiPolygon`, both exterior and interior rings are converted.
    - Interior rings (holes) are included as subpaths with `CLOSEPOLY` codes.
    - For `LineString`, a single open path is created.

    See Also
    --------
    matplotlib.patches.PathPatch
    shapely.geometry.Polygon
    shapely.geometry.MultiPolygon
    shapely.geometry.LineString
    """

    def polygon_to_paths(polygon: Polygon) -> list[Path]:
        paths = []

        # Exterior ring
        ext_coords = np.asarray(polygon.exterior.coords)
        ext_codes = [Path.MOVETO] + [Path.LINETO] * (len(ext_coords) - 2) + [Path.CLOSEPOLY]
        paths.append(Path(ext_coords, ext_codes))

        # Interior rings (holes)
        for interior in polygon.interiors:
            int_coords = np.asarray(interior.coords)
            int_codes = [Path.MOVETO] + [Path.LINETO] * (len(int_coords) - 2) + [Path.CLOSEPOLY]
            paths.append(Path(int_coords, int_codes))

        return paths

    if geom.geom_type == "Polygon":
        paths = polygon_to_paths(geom)
        path = Path.make_compound_path(*paths)

    elif geom.geom_type == "MultiPolygon":
        all_paths = []
        for poly in geom.geoms:
            all_paths.extend(polygon_to_paths(poly))
        path = Path.make_compound_path(*all_paths)

    elif geom.geom_type == "LineString":
        coords = np.asarray(geom.coords)
        codes = [Path.MOVETO] + [Path.LINETO] * (len(coords) - 1)
        path = Path(coords, codes)

    else:
        raise NotImplementedError(f"Geometry type {geom.geom_type} is not supported.")

    # Color copying
    fc = template_patch.get_facecolor() if template_patch else "black"
    ec = template_patch.get_edgecolor() if template_patch else "none"

    return PathPatch(path, facecolor=fc, edgecolor=ec, linewidth=0.0)


def union(patch1: PathPatch, patch2: PathPatch) -> PathPatch:
    """
    Compute the union of two Matplotlib PathPatches using Shapely.

    This function converts two Matplotlib `PathPatch` objects into Shapely geometries,
    computes their union, and then converts the result back into a `PathPatch`.
    This is useful for merging overlapping or adjacent patches into a single patch.

    Parameters
    ----------
    patch1 : matplotlib.patches.PathPatch
        The first patch to union.
    patch2 : matplotlib.patches.PathPatch
        The second patch to union.

    Returns
    -------
    matplotlib.patches.PathPatch
        A new `PathPatch` representing the union of `patch1` and `patch2`.
        Visual properties (facecolor and edgecolor) are inherited from `patch1`.

    See Also
    --------
    _pathpatch_to_shapely : Converts a PathPatch to a Shapely geometry.
    _shapely_to_pathpatch : Converts a Shapely geometry to a PathPatch.
    """
    geom1 = _pathpatch_to_shapely(patch1)
    geom2 = _pathpatch_to_shapely(patch2)
    result = geom1.union(geom2)
    return _shapely_to_pathpatch(result, template_patch=patch1)


def difference(patch1: PathPatch, patch2: PathPatch) -> PathPatch:
    """
    Compute the geometric difference between two PathPatches (patch1 - patch2).

    Converts both `PathPatch` objects to Shapely geometries, computes the difference
    (i.e., the area of `patch1` excluding the overlap with `patch2`), and converts
    the result back into a `PathPatch` for visualization.

    Parameters
    ----------
    patch1 : matplotlib.patches.PathPatch
        The patch from which geometry will be subtracted.
    patch2 : matplotlib.patches.PathPatch
        The patch to subtract from `patch1`.

    Returns
    -------
    matplotlib.patches.PathPatch
        A new `PathPatch` representing the geometric difference `patch1 - patch2`.
        Visual properties (facecolor and edgecolor) are inherited from `patch1`.

    See Also
    --------
    union : Computes the union of two patches.
    _pathpatch_to_shapely : Converts a PathPatch to a Shapely geometry.
    _shapely_to_pathpatch : Converts a Shapely geometry to a PathPatch.
    """
    geom1 = _pathpatch_to_shapely(patch1)
    geom2 = _pathpatch_to_shapely(patch2)
    result = geom1.difference(geom2)
    return _shapely_to_pathpatch(result, template_patch=patch1)


def intersection(patch1: PathPatch, patch2: PathPatch) -> PathPatch:
    """
    Compute the geometric intersection of two PathPatches using Shapely.

    Converts both `PathPatch` objects into Shapely geometries, computes the
    intersection (i.e., the overlapping region), and returns it as a new `PathPatch`.

    Parameters
    ----------
    patch1 : matplotlib.patches.PathPatch
        The first patch for the intersection.
    patch2 : matplotlib.patches.PathPatch
        The second patch for the intersection.

    Returns
    -------
    matplotlib.patches.PathPatch
        A new `PathPatch` representing the intersection of `patch1` and `patch2`.
        Visual properties (facecolor and edgecolor) are inherited from `patch1`.

    See Also
    --------
    union : Computes the union of two patches.
    difference : Computes the difference between two patches.
    _pathpatch_to_shapely : Converts a PathPatch to a Shapely geometry.
    _shapely_to_pathpatch : Converts a Shapely geometry to a PathPatch.
    """
    geom1 = _pathpatch_to_shapely(patch1)
    geom2 = _pathpatch_to_shapely(patch2)
    result = geom1.intersection(geom2)
    return _shapely_to_pathpatch(result, template_patch=patch1)


def unary_union(patches: list[PathPatch]) -> PathPatch:
    """
    Compute the geometric union of a list of PathPatches using Shapely.

    Converts each `PathPatch` in the list to a Shapely geometry, performs a unary union
    (i.e., merges all patches into a single shape), and converts the result back to a
    single `PathPatch`.

    Parameters
    ----------
    patches : list of matplotlib.patches.PathPatch
        A list of PathPatch objects to union. Must contain at least one patch.

    Returns
    -------
    matplotlib.patches.PathPatch
        A new `PathPatch` representing the union of all input patches.
        Visual properties (facecolor and edgecolor) are inherited from the first patch.

    Raises
    ------
    IndexError
        If the input list is empty.

    See Also
    --------
    union : Computes the union of two patches.
    shapely.ops.unary_union : Performs the union operation on Shapely geometries.
    _pathpatch_to_shapely : Converts a PathPatch to a Shapely geometry.
    _shapely_to_pathpatch : Converts a Shapely geometry to a PathPatch.
    """
    geoms = [_pathpatch_to_shapely(patch) for patch in patches]
    result = shapely_unary_union(geoms)
    return _shapely_to_pathpatch(result, template_patch=patches[0])


def scale(patch: PathPatch, xfact=1.0, yfact=1.0, origin=(0.0, 0.0)) -> PathPatch:
    """
    Scale a PathPatch using Shapely geometric scaling.

    This function converts a `PathPatch` to a Shapely geometry, applies a scaling
    transformation about a specified origin, and then converts the result back
    to a `PathPatch`. Supports negative scale factors for axis mirroring.
    Attempts to preserve polygon ring orientation.

    Parameters
    ----------
    patch : matplotlib.patches.PathPatch
        The patch to scale.
    xfact : float, optional
        Scaling factor in the x-direction. Defaults to 1.0.
    yfact : float, optional
        Scaling factor in the y-direction. Defaults to 1.0.
    origin : tuple of float, optional
        The (x, y) coordinates to scale around. Defaults to (0.0, 0.0).

    Returns
    -------
    matplotlib.patches.PathPatch
        A new `PathPatch` representing the scaled geometry.
        Visual properties (facecolor and edgecolor) are inherited from the original patch.

    Notes
    -----
    - Negative scale factors result in axis mirroring.
    - For `Polygon` and `MultiPolygon`, the exterior ring orientation is preserved
      after scaling using `shapely.geometry.orient`.
    - Uses `shapely.affinity.scale` under the hood.

    See Also
    --------
    shapely.affinity.scale : Applies affine scaling to Shapely geometries.
    shapely.geometry.orient : Reorients polygon rings for proper winding.
    """
    original = _pathpatch_to_shapely(patch)
    scaled = affinity.scale(original, xfact=xfact, yfact=yfact, origin=origin)

    def match_orientation(scaled_part, original_part):
        # Match exterior ring direction (holes are handled automatically)
        target_sign = 1.0 if original_part.exterior.is_ccw else -1.0
        return orient(scaled_part, sign=target_sign)

    if isinstance(original, Polygon) and isinstance(scaled, Polygon):
        scaled = match_orientation(scaled, original)

    elif isinstance(original, MultiPolygon) and isinstance(scaled, MultiPolygon):
        scaled = MultiPolygon(
            [
                match_orientation(scaled_part, original_part)
                for scaled_part, original_part in zip(scaled.geoms, original.geoms)
            ]
        )

    # fallback — no orientation fix
    return _shapely_to_pathpatch(scaled, template_patch=patch)


def rotate(patch: PathPatch, angle=0.0, origin=(0.0, 0.0), use_radians=False) -> PathPatch:
    """
    Rotate a PathPatch using Shapely geometric rotation.

    Converts a `PathPatch` into a Shapely geometry, applies a 2D rotation
    around a specified origin, and converts the result back into a `PathPatch`.

    Parameters
    ----------
    patch : matplotlib.patches.PathPatch
        The patch to rotate.
    angle : float, optional
        The angle of rotation. By default, this is interpreted in degrees.
    origin : tuple of float, optional
        The (x, y) coordinates of the rotation center. Defaults to (0.0, 0.0).
    use_radians : bool, optional
        If True, the `angle` is interpreted in radians. Defaults to False (degrees).

    Returns
    -------
    matplotlib.patches.PathPatch
        A new `PathPatch` representing the rotated geometry.
        Visual properties (facecolor and edgecolor) are inherited from the original patch.

    See Also
    --------
    shapely.affinity.rotate : Applies a rotation to Shapely geometries.
    scale : Scales a patch around an origin.
    """

    geom = _pathpatch_to_shapely(patch)
    rotated = affinity.rotate(geom, angle, origin=origin, use_radians=use_radians)
    return _shapely_to_pathpatch(rotated, template_patch=patch)


def translate(patch: PathPatch, dr=(0.0, 0.0)) -> PathPatch:
    """
    Translate a PathPatch using Shapely geometric translation.

    Converts a `PathPatch` into a Shapely geometry, applies a 2D translation
    (offset) by the specified delta in x and y, and returns the translated
    geometry as a new `PathPatch`.

    Parameters
    ----------
    patch : matplotlib.patches.PathPatch
        The patch to translate.
    dr : tuple of float, optional
        The translation vector `(dx, dy)` to apply. Defaults to (0.0, 0.0).

    Returns
    -------
    matplotlib.patches.PathPatch
        A new `PathPatch` representing the translated geometry.
        Visual properties (facecolor and edgecolor) are inherited from the original patch.

    See Also
    --------
    shapely.affinity.translate : Applies translation to Shapely geometries.
    rotate : Rotates a patch about an origin.
    scale : Scales a patch about an origin.
    """

    dx, dy = dr
    geom = _pathpatch_to_shapely(patch)
    translated = affinity.translate(geom, xoff=dx, yoff=dy)
    return _shapely_to_pathpatch(translated, template_patch=patch)


def deform(patch: PathPatch, func):
    """
    Apply a deformation function to the vertices of a PathPatch.

    This function modifies the shape of a `PathPatch` by applying a user-defined
    transformation to its vertices. The path codes (e.g., MOVETO, LINETO) are preserved,
    and visual properties such as facecolor and edgecolor are copied from the original patch.

    Parameters
    ----------
    patch : matplotlib.patches.PathPatch
        The patch to deform.
    func : callable
        A function that takes an (N, 2) NumPy array of vertices and returns
        a transformed (N, 2) array of the same shape.

    Returns
    -------
    matplotlib.patches.PathPatch
        A new `PathPatch` with the transformed geometry and inherited style.

    Notes
    -----
    - This version does not perform Bézier resampling, so curvature is not introduced
      unless present in the original path.
    - If deformation includes perspective or nonlinear mappings, consider using
      a denser or resampled path for better fidelity.

    See Also
    --------
    matplotlib.path.Path
    """
    path = patch.get_path()
    verts = path.vertices
    codes = path.codes
    new_vertices = func(verts)
    new_path = Path(new_vertices, codes)

    # Color copying
    fc = patch.get_facecolor()
    ec = patch.get_edgecolor()

    return PathPatch(new_path, facecolor=fc, edgecolor=ec)


def flip_x(patch: PathPatch, origin=(0.0, 0.0)) -> PathPatch:
    """
    Flips a PathPatch across the x-axis without unioning it with the original.

    Parameters
    ----------
    patch : matplotlib.patches.PathPatch
        The patch to mirror.
    origin : tuple of float, optional
        The (x, y) origin point to mirror about. Defaults to (0.0, 0.0).

    Returns
    -------
    matplotlib.patches.PathPatch
        A new patch containing the union of the original and its x-axis mirror.
    """
    return scale(patch, xfact=-1.0, yfact=1.0, origin=origin)


def flip_y(patch: PathPatch, origin=(0.0, 0.0)) -> PathPatch:
    """
    Flips a PathPatch across the y-axis without unioning it with the original.

    Parameters
    ----------
    patch : matplotlib.patches.PathPatch
        The patch to mirror.
    origin : tuple of float, optional
        The (x, y) origin point to mirror about. Defaults to (0.0, 0.0).

    Returns
    -------
    matplotlib.patches.PathPatch
        A new patch containing the union of the original and its x-axis mirror.
    """
    return scale(patch, xfact=1.0, yfact=-1.0, origin=origin)


def flip_xy(patch: PathPatch, origin=(0.0, 0.0)) -> PathPatch:
    """
    Flips a PathPatch across the y and y axes without unioning it with the original.

    Parameters
    ----------
    patch : matplotlib.patches.PathPatch
        The patch to mirror.
    origin : tuple of float, optional
        The (x, y) origin point to mirror about. Defaults to (0.0, 0.0).

    Returns
    -------
    matplotlib.patches.PathPatch
        A new patch containing the union of the original and its x-axis mirror.
    """
    return scale(patch, xfact=-1.0, yfact=-1.0, origin=origin)


def mirror_x(patch: PathPatch, origin=(0.0, 0.0)) -> PathPatch:
    """
    Reflect a PathPatch across the x-axis and union it with the original.

    Parameters
    ----------
    patch : matplotlib.patches.PathPatch
        The patch to mirror.
    origin : tuple of float, optional
        The (x, y) origin point to mirror about. Defaults to (0.0, 0.0).

    Returns
    -------
    matplotlib.patches.PathPatch
        A new patch containing the union of the original and its x-axis mirror.
    """
    return union(patch, flip_x(patch))


def mirror_y(patch: PathPatch, origin=(0.0, 0.0)) -> PathPatch:
    """
    Reflect a PathPatch across the y-axis and union it with the original.

    Parameters
    ----------
    patch : matplotlib.patches.PathPatch
        The patch to mirror.
    origin : tuple of float, optional
        The (x, y) origin point to mirror about. Defaults to (0.0, 0.0).

    Returns
    -------
    matplotlib.patches.PathPatch
        A new patch containing the union of the original and its y-axis mirror.
    """
    return union(patch, flip_y(patch))


def mirror_xy(patch: PathPatch, origin=(0.0, 0.0)) -> PathPatch:
    """
    Reflect a PathPatch across both x- and y-axes and union with all versions.

    This is equivalent to mirroring across both axes and combining the result
    with the original shape.

    Parameters
    ----------
    patch : matplotlib.patches.PathPatch
        The patch to mirror.
    origin : tuple of float, optional
        The (x, y) origin point to mirror about. Defaults to (0.0, 0.0).

    Returns
    -------
    matplotlib.patches.PathPatch
        A new patch containing the union of the original and its full mirrored set.
    """
    return mirror_y(mirror_x(patch, origin=origin), origin=origin)


def mirror(patch: PathPatch, axis: str = "x", origin=(0.0, 0.0)) -> PathPatch:
    """
    Reflect a PathPatch across a specified axis or both, and union with the original.

    Parameters
    ----------
    patch : matplotlib.patches.PathPatch
        The patch to mirror.
    axis : {'x', 'y', 'both', 'xy'}, optional
        The axis or axes to mirror across. Defaults to 'x'.
    origin : tuple of float, optional
        The (x, y) origin point to mirror about. Defaults to (0.0, 0.0).

    Returns
    -------
    matplotlib.patches.PathPatch
        A new patch containing the union of the original and its mirrored counterpart(s).

    Raises
    ------
    ValueError
        If `axis` is not one of 'x', 'y', or 'both'/'xy'.

    See Also
    --------
    mirror_x : Reflect across the x-axis.
    mirror_y : Reflect across the y-axis.
    mirror_xy : Reflect across both axes.
    """
    if axis == "x":
        return mirror_x(patch, origin)
    elif axis == "y":
        return mirror_y(patch, origin)
    elif axis == "both" or axis == "xy":
        return mirror_xy(patch, origin)
    else:
        raise ValueError("axis must be 'x', 'y', or 'both'")


def buffer_path(
    path: Path,
    buffer_amount: float,
    *,
    style: EdgeStyle = EdgeStyle.FLAT,
    samples_per_segment: int = 50,
    side: str = "both",  # 'both', 'left', or 'right'
) -> PathPatch:
    """
    Buffers a Path using Shapely and returns a PathPatch.

    Supports both symmetric (around the line) and one-sided buffering.
    One-sided buffers follow the direction of the path:
    - 'left': buffer on the left side of the path
    - 'right': buffer on the right side (negative buffer)
    - 'both': standard symmetric buffer

    Parameters
    ----------
    path : matplotlib.path.Path
        The path to buffer.
    buffer_amount : float
        The distance to buffer. Positive values grow the geometry outward.
    style : EdgeStyle, optional
        The style of caps and joins (flat, round, square). Default is FLAT.
    samples_per_segment : int, optional
        Number of linear segments to use per Bézier curve when resampling. Default is 50.
    side : {'both', 'left', 'right'}, optional
        Which side to apply the buffer on. Default is 'both'.

    Returns
    -------
    matplotlib.patches.PathPatch
        A PathPatch representing the buffered geometry.

    Raises
    ------
    ValueError
        If `side` is not one of {'both', 'left', 'right'}.

    See Also
    --------
    shapely.geometry.LineString.buffer
    """

    if side not in {"both", "left", "right"}:
        raise ValueError("side must be one of {'both', 'left', 'right'}")

    resampled_path = resample_path(path, samples_per_segment)
    geom = LineString(resampled_path.vertices)

    single_sided = side in {"left", "right"}
    amount = buffer_amount if side != "right" else -buffer_amount

    buffered = geom.buffer(
        amount,
        cap_style=style.value,
        join_style=style.value,
        single_sided=single_sided,
    )

    return _shapely_to_pathpatch(buffered)


def outline_path(
    path: Path,
    width: float,
    side: str = "center",  # options: 'center', 'inside', 'outside'
    samples_per_segment: int = 50,
    style: EdgeStyle = EdgeStyle.FLAT,
) -> PathPatch:
    """
    Returns a PathPatch representing a stroked outline of the path.

    Parameters
    ----------
    path : matplotlib.path.Path
        The shape path to outline.
    width : float
        Total stroke width.
    side : {'center', 'inside', 'outside'}
        Where to apply the stroke relative to the original shape boundary.
    samples_per_segment : int
        Number of segments for Bézier resampling.
    style : EdgeStyle
        Cap and join style.

    Returns
    -------
    PathPatch
        Patch representing the outline as a filled region.
    """
    if side not in {"center", "inside", "outside"}:
        raise ValueError("side must be 'center', 'inside', or 'outside'")

    verts = resample_path(path, samples_per_segment).vertices
    is_closed = np.allclose(verts[0], verts[-1])

    if is_closed:
        polygon = Polygon(verts)

        if side == "center":
            outer = polygon.buffer(width / 2, cap_style=style.value, join_style=style.value)
            inner = polygon.buffer(-width / 2, cap_style=style.value, join_style=style.value)
        elif side == "outside":
            outer = polygon.buffer(width, cap_style=style.value, join_style=style.value)
            inner = polygon
        elif side == "inside":
            outer = polygon
            inner = polygon.buffer(-width, cap_style=style.value, join_style=style.value)

        stroked = outer.difference(inner)

    else:
        line = LineString(verts)
        # For open paths, the only real option is 'center' stroke (symmetric)
        if side != "center":
            raise ValueError("Open paths only support 'center' stroke.")
        stroked = line.buffer(width / 2, cap_style=style.value, join_style=style.value)

    return _shapely_to_pathpatch(stroked)


def outline(
    patch: PathPatch,
    *,
    width=1.0,
    color="black",
    style: EdgeStyle = EdgeStyle.FLAT,
    samples_per_segment=50,
    side: str = "center",  # options: 'center', 'inside', 'outside'
) -> PathPatch:
    """
    Create a visual outline (stroke) around a PathPatch.

    This function buffers the patch's path to simulate a stroked outline with a
    specified width. Supports symmetric (default) or one-sided outlines, and
    allows control over cap and join style.

    Parameters
    ----------
    patch : matplotlib.patches.PathPatch
        The patch whose outline will be rendered.
    width : float, optional
        The total stroke width in data units. Default is 1.0.
    color : str or tuple, optional
        The facecolor to apply to the outline patch. Default is "black".
    style : EdgeStyle, optional
        The cap and join style to use (FLAT, ROUND, SQUARE). Default is FLAT.
    samples_per_segment : int, optional
        Number of linear segments per Bézier when resampling. Default is 50.
    side : {'both', 'left', 'right'}, optional
        Which side of the path to place the outline on. 'both' applies a full
        symmetric stroke. 'left' and 'right' apply one-sided strokes based on path direction.

    Returns
    -------
    matplotlib.patches.PathPatch
        A new `PathPatch` representing the stroked outline geometry.

    Raises
    ------
    ValueError
        If `side` is not one of {'both', 'left', 'right'}.

    See Also
    --------
    buffer_path : General buffering utility for arbitrary paths.
    """
    # Transform the patch's path first
    transformed_path = patch.get_transform().transform_path(patch.get_path())

    # Use the buffer_path utility to apply the actual buffering
    outline_patch = outline_path(
        transformed_path,
        width=width,
        side=side,
        samples_per_segment=samples_per_segment,
        style=style,
    )

    outline_patch.set_facecolor(color)
    outline_patch.set_edgecolor("none")

    return outline_patch


""" 
============= ============= ============= ============= ============= =============
                                LIST OF SHAPES
============= ============= ============= ============= ============= =============
"""


def FilledCircle(center, radius, color="black", resolution=64):
    """
    Create a filled circular PathPatch using Shapely's buffer around a point.

    This function generates a circular patch centered at a given point by
    buffering a Shapely `Point` and converting the result into a `PathPatch`.
    The resolution controls the smoothness of the circle approximation.

    Parameters
    ----------
    center : tuple of float
        The (x, y) coordinates of the circle's center.
    radius : float
        The radius of the circle.
    color : str or tuple, optional
        The facecolor of the circle. Default is "black".
    resolution : int, optional
        The number of segments used to approximate the circle's boundary.
        Higher values produce smoother circles. Default is 64.

    Returns
    -------
    matplotlib.patches.PathPatch
        A filled circular patch with no edge.

    See Also
    --------
    shapely.geometry.Point.buffer : Used to construct the circle geometry.
    _shapely_to_pathpatch : Converts the buffered shape into a patch.
    """
    circle_geom = Point(center).buffer(radius, resolution=resolution)
    patch = _shapely_to_pathpatch(circle_geom)
    patch.set_facecolor(color)
    patch.set_edgecolor("none")
    return patch


def OutlineCircle(center, radius, linewidth, color="black", resolution=64):
    """
    Create a ring-shaped (outlined) circular PathPatch using Shapely buffering.

    This function constructs an annulus (ring) centered at the given point
    by subtracting a smaller inner circle from a larger outer circle.
    Useful for rendering outlined circles with controllable stroke width.

    Parameters
    ----------
    center : tuple of float
        The (x, y) coordinates of the circle's center.
    radius : float
        The radius of the central path. The outline is drawn around this radius.
    linewidth : float
        The thickness of the outline (ring width).
    color : str or tuple, optional
        The facecolor of the ring. Default is "black".
    resolution : int, optional
        Number of segments used to approximate the circle boundary.
        Higher values yield smoother curves. Default is 64.

    Returns
    -------
    matplotlib.patches.PathPatch
        A PathPatch representing a filled ring (annulus), centered at `center`.

    See Also
    --------
    FilledCircle : Creates a solid circle.
    shapely.geometry.Point.buffer : Underlying geometry builder.
    """
    # Step 1: Create the outline as a LineString buffer
    inner_circle = Point(center).buffer(radius - linewidth / 2, resolution=resolution)
    outer_circle = Point(center).buffer(radius + linewidth / 2, resolution=resolution)

    annulus = outer_circle.difference(inner_circle)

    # Step 2: Convert to PathPatch
    patch = _shapely_to_pathpatch(annulus)
    patch.set_facecolor(color)
    patch.set_edgecolor("none")
    return patch


def Sector(center, radius, theta1, theta2, color="black", num_segments=64):
    """
    Create a filled circular sector (pie slice) using a chord to close the arc.

    This function generates a sector shape by tracing an arc from `theta1` to `theta2`
    and connecting its endpoints directly (via a chord), rather than connecting to the origin.
    The resulting geometry is translated to the specified center and returned as a PathPatch.

    Parameters
    ----------
    center : tuple of float
        The (x, y) coordinates of the sector's center.
    radius : float
        The radius of the arc.
    theta1 : float
        Starting angle of the arc in degrees.
    theta2 : float
        Ending angle of the arc in degrees.
    color : str or tuple, optional
        The facecolor of the sector. Default is "black".
    num_segments : int, optional
        Number of points used to approximate the arc. Higher values yield smoother curves.
        Default is 64.

    Returns
    -------
    matplotlib.patches.PathPatch
        A PathPatch representing the sector (pie slice), closed by a straight line (chord).

    Notes
    -----
    - Angles are interpreted in degrees and follow the standard counterclockwise
      direction from the positive x-axis.
    - The resulting polygon is closed automatically and oriented for consistent rendering.

    See Also
    --------
    shapely.geometry.Polygon : Used to construct the sector geometry.
    shapely.affinity.translate : Used to position the shape.
    """
    cx, cy = center
    theta = np.radians(np.linspace(theta1, theta2, num_segments))

    arc_x = radius * np.cos(theta)
    arc_y = radius * np.sin(theta)
    arc = np.column_stack([arc_x, arc_y])

    # Create polygon, translate to center, clean geometry
    sector_geom = Polygon(arc)
    sector_geom = affinity.translate(sector_geom, xoff=cx, yoff=cy)
    sector_geom = orient(sector_geom, 1)

    patch = _shapely_to_pathpatch(sector_geom)
    patch.set_facecolor(color)
    patch.set_edgecolor("none")
    return patch


def ArcPatch(center, radius, theta1, theta2, linewidth, color="black", resolution=100):
    """
    Create a filled arc segment (ring slice) as a PathPatch.

    This function generates a stroked arc by tracing both an outer and inner arc,
    then connecting them into a closed ring segment. The stroke is centered at
    the given radius and has a specified `linewidth`.

    Parameters
    ----------
    center : tuple of float
        The (x, y) coordinates of the arc's center.
    radius : float
        The inner radius of the arc. The stroke is drawn outward from this radius.
    theta1 : float
        Starting angle of the arc in degrees.
    theta2 : float
        Ending angle of the arc in degrees.
    linewidth : float
        Thickness of the arc segment (stroke width).
    color : str or tuple, optional
        Fill color of the arc. Default is "black".
    resolution : int, optional
        Number of points used to approximate each arc. Default is 100.

    Returns
    -------
    matplotlib.patches.PathPatch
        A `PathPatch` representing the filled arc segment.

    Notes
    -----
    - Angles are interpreted in degrees, counterclockwise from the positive x-axis.
    - The path is constructed manually using two arcs (outer and inner, reversed) and closed.
    - This is equivalent to a stroked arc but created explicitly for flexible styling.

    See Also
    --------
    Sector : Creates a pie-slice shape closed by a chord.
    OutlineCircle : Creates a full circular ring.
    matplotlib.path.Path : Used to define the arc geometry.
    """
    cx, cy = center
    theta1_rad = np.deg2rad(theta1)
    theta2_rad = np.deg2rad(theta2)

    # Outer arc (radius + linewidth)
    theta_outer = np.linspace(theta1_rad, theta2_rad, resolution)
    x_outer = cx + (radius + linewidth) * np.cos(theta_outer)
    y_outer = cy + (radius + linewidth) * np.sin(theta_outer)

    # Inner arc (radius), reversed
    theta_inner = np.linspace(theta2_rad, theta1_rad, resolution)
    x_inner = cx + radius * np.cos(theta_inner)
    y_inner = cy + radius * np.sin(theta_inner)

    # Combine points
    vertices = np.vstack(
        [
            np.column_stack((x_outer, y_outer)),
            np.column_stack((x_inner, y_inner)),
            np.column_stack([x_outer[0], y_outer[0]]),  # Close path
        ]
    )

    codes = [Path.MOVETO] + [Path.LINETO] * (len(vertices) - 2) + [Path.CLOSEPOLY]
    path = Path(vertices, codes)
    return PathPatch(path, facecolor=color, edgecolor="none", linewidth=0.0)


def LinePatch(xdata, ydata, linewidth, color="black", style=EdgeStyle.ROUND):
    """
    Create a thick line segment between two points as a filled PathPatch.

    This function generates a polygonal representation of a line segment
    with thickness, using Shapely's buffer method. Cap and join styles are
    configurable. The resulting patch can be styled and added to any Matplotlib axis.

    Parameters
    ----------
    xdata : list or tuple of float
        The x-coordinates of the two endpoints (length must be 2).
    ydata : list or tuple of float
        The y-coordinates of the two endpoints (length must be 2).
    linewidth : float
        Total width of the line. The buffer radius is `linewidth / 2`.
    color : str or tuple, optional
        Fill color of the line. Default is "black".
    style : EdgeStyle, optional
        Style of line caps and joins (e.g., ROUND, FLAT, SQUARE). Default is ROUND.

    Returns
    -------
    matplotlib.patches.PathPatch
        A `PathPatch` representing the thickened line segment.

    Raises
    ------
    ValueError
        If `xdata` and `ydata` do not contain exactly two elements.

    See Also
    --------
    shapely.geometry.LineString.buffer : Used to create the polygonal stroke.
    _shapely_to_pathpatch : Converts buffered geometry to a patch.
    """
    points = list(zip(xdata, ydata))
    line = LineString(points)
    buffered = line.buffer(linewidth / 2.0, cap_style=style.value, join_style=style.value)

    patch = _shapely_to_pathpatch(buffered)
    patch.set_facecolor(color)
    patch.set_edgecolor("none")
    patch.set_linewidth(0.0)  # No edge line
    return patch


def RectanglePatch(xy, width, height, color):
    """
    Create a filled rectangular PathPatch.

    This function creates a rectangle with the given origin, width, height, and fill color,
    using Matplotlib's built-in `patches.Rectangle`.

    Parameters
    ----------
    xy : tuple of float
        The (x, y) coordinates of the bottom-left corner of the rectangle.
    width : float
        Width of the rectangle.
    height : float
        Height of the rectangle.
    color : str or tuple
        The fill color of the rectangle.

    Returns
    -------
    matplotlib.patches.Rectangle
        A `Rectangle` patch with the specified geometry and facecolor.

    See Also
    --------
    matplotlib.patches.Rectangle : Underlying class used to draw the shape.
    """

    rect = patches.Rectangle(
        xy,
        width,
        height,
        facecolor=color,
        edgecolor="none",
        linewidth=0.0,
    )
    return rect


def FilledPolygon(points, color):
    """
    Create a filled polygonal PathPatch from a sequence of points.

    This function constructs a closed polygon using the provided vertices,
    and returns a filled `Polygon` patch with the specified facecolor.

    Parameters
    ----------
    points : array-like of shape (N, 2)
        A sequence of (x, y) coordinates defining the polygon vertices.
    color : str or tuple
        The fill color of the polygon.

    Returns
    -------
    matplotlib.patches.Polygon
        A `Polygon` patch representing the filled shape.

    See Also
    --------
    matplotlib.patches.Polygon : Used to render the shape.
    """
    poly = patches.Polygon(
        points,
        closed=True,
        facecolor=color,
        linewidth=0.0,
    )
    return poly


def Wedge(xy, radius, theta1, theta2, color):
    """
    Create a filled wedge (pie slice) as a PathPatch.

    This function constructs a wedge shape (circular sector that connects to the center)
    using Matplotlib’s `Wedge` patch. The shape is defined by two angles and a radius.

    Parameters
    ----------
    xy : tuple of float
        The (x, y) coordinates of the center of the wedge.
    radius : float
        The radius of the wedge.
    theta1 : float
        Starting angle of the wedge in degrees.
    theta2 : float
        Ending angle of the wedge in degrees.
    color : str or tuple
        The fill color of the wedge.

    Returns
    -------
    matplotlib.patches.Wedge
        A `Wedge` patch representing the filled sector.

    See Also
    --------
    Sector : Like Wedge, but closes with a chord (not to the origin).
    matplotlib.patches.Wedge : Underlying class used to construct the shape.
    """
    wedge = patches.Wedge(
        xy,
        radius,
        theta1,
        theta2,
        facecolor=color,
        linewidth=0.0,
    )
    return wedge


def RoundedRectangle(xy, width, height, corner_radius, color):
    """
    Create a filled rectangle with rounded corners using FancyBboxPatch.

    This function constructs a rectangle centered at the origin, with the specified
    width and height, and applies rounded corners using the `rounding_size` parameter.

    Parameters
    ----------
    xy : tuple of float
        The (x, y) center of the rectangle. (Note: currently unused — shape is centered at origin.)
    width : float
        Width of the rectangle.
    height : float
        Height of the rectangle.
    corner_radius : float
        Radius of the rounded corners.
    color : str or tuple
        Fill color of the rectangle.

    Returns
    -------
    matplotlib.patches.FancyBboxPatch
        A patch representing a filled, rounded rectangle.

    Notes
    -----
    - The rectangle is centered at (0, 0). You can position it using `set_xy()` or transforms.
    - The `xy` parameter is currently ignored in placement; it's included for future use.

    See Also
    --------
    matplotlib.patches.FancyBboxPatch : Underlying patch class.
    RectanglePatch : Creates a regular (non-rounded) rectangle.
    """
    rectangle = patches.FancyBboxPatch(
        (-width / 2, -height / 2),
        width,
        height,
        boxstyle=f"round,pad=0,rounding_size={corner_radius}",
        edgecolor="none",
        facecolor=color,
        linewidth=0.0,
    )
    return _shapely_to_pathpatch(orient(_pathpatch_to_shapely(rectangle), -1), rectangle)
