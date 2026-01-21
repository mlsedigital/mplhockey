from mplhockey.geometry import *


def OuterBoards(ice_width, ice_height, boards_width, corner_radius, color):
    """
    Create a rounded rectangle representing the outer boards of a hockey rink.

    This function returns a `PathPatch` for the rink's perimeter boards, which
    are modeled as a rounded rectangle surrounding the ice surface. The boards
    extend outward from the ice dimensions by `boards_width` in both directions,
    and have rounded corners specified by `corner_radius`.

    Parameters
    ----------
    ice_width : float
        Width of the main ice surface (in rink units, e.g., feet or meters).
    ice_height : float
        Height of the main ice surface.
    boards_width : float
        Thickness of the boards surrounding the ice.
    corner_radius : float
        Radius of the rounded corners on the boards.
    color : str or tuple
        Fill color of the boards.

    Returns
    -------
    matplotlib.patches.FancyBboxPatch
        A patch representing the outer boards as a rounded rectangle.

    See Also
    --------
    RoundedRectangle : Underlying function used to build the shape.
    """
    ice = RoundedRectangle((0.0, 0.0), ice_width, ice_height, corner_radius, color="white")
    boards = outline(ice, width=boards_width, color=color, side="outside")
    return boards


def IceSurface(ice_width, ice_height, corner_radius, color):
    """
    Create a rounded rectangle representing the playable ice surface.

    This function returns a `PathPatch` for the main ice surface area,
    modeled as a rounded rectangle with specified width, height, and corner curvature.

    Parameters
    ----------
    ice_width : float
        Width of the ice surface (in rink units, e.g., feet or meters).
    ice_height : float
        Height of the ice surface.
    corner_radius : float
        Radius of the rounded corners on the rink.
    color : str or tuple
        Fill color of the ice surface.

    Returns
    -------
    matplotlib.patches.FancyBboxPatch
        A patch representing the playable ice surface.

    See Also
    --------
    OuterBoards : Builds the perimeter boards around the ice.
    RoundedRectangle : Used internally to generate the rounded shape.
    """
    return RoundedRectangle((0.0, 0.0), ice_width, ice_height, corner_radius, color)


def VLinePatch(x_pos, linewidth, color, length=85.0, y_pos=0.0):
    """
    Create a vertical rink line (e.g., blue line, red line) as a thickened patch.

    This function draws a vertical line at a specified x-position, extending
    vertically to the given length and rendered with the specified thickness and color.

    Parameters
    ----------
    x_pos : float
        The x-coordinate at which to center the vertical line.
    linewidth : float
        The total width of the line (thickening occurs symmetrically).
    color : str or tuple
        Fill color of the line.
    length : float, optional
        Total vertical extent of the line, centered at y = 0. Default is 85.0 (standard rink length).

    Returns
    -------
    matplotlib.patches.PathPatch
        A patch representing the vertical line segment with specified thickness.

    See Also
    --------
    LinePatch : General-purpose function used to construct the shape.
    """
    return LinePatch([x_pos, x_pos], [y_pos - length / 2, y_pos + length / 2], linewidth, color)


def HLinePatch(y_pos, linewidth, color, length=85.0):
    """
    Create a horizontal rink line (e.g., goal line, trapezoid base) as a thickened patch.

    This function draws a horizontal line at a specified y-position, extending
    horizontally to the given length and rendered with the specified thickness and color.

    Parameters
    ----------
    y_pos : float
        The y-coordinate at which to center the horizontal line.
    linewidth : float
        The total width of the line (thickening occurs symmetrically).
    color : str or tuple
        Fill color of the line.
    length : float, optional
        Total horizontal extent of the line, centered at x = 0. Default is 85.0 (standard rink width).

    Returns
    -------
    matplotlib.patches.PathPatch
        A patch representing the horizontal line segment with specified thickness.

    See Also
    --------
    LinePatch : General-purpose function used to construct the shape.
    VLinePatch : Vertical version of this function.
    """

    return LinePatch([-length / 2, length / 2], [y_pos, y_pos], linewidth, color)


def RinkCircle(position, radius, color):
    """
    Create a filled circle on the rink (e.g., faceoff dot or center circle).

    This function wraps `FilledCircle` for hockey-specific purposes, producing
    a circular patch at a given position with a specified radius and color.

    Parameters
    ----------
    position : tuple of float
        The (x, y) coordinates of the circle's center.
    radius : float
        Radius of the circle.
    color : str or tuple
        Fill color of the circle.

    Returns
    -------
    matplotlib.patches.PathPatch
        A patch representing a filled circle.

    See Also
    --------
    FilledCircle : Underlying function used to build the shape.
    OutlineCircle : For stroked (ring-shaped) circles.
    """
    return FilledCircle(position, radius, color)


def RinkCircleOutline(position, radius, linewidth, color):
    """
    Create an outlined rink circle (ring) for hockey diagrams.

    This function wraps `OutlineCircle` to generate a ring-shaped patch at the specified
    position, useful for center ice circles, faceoff circles, or other rink markings.

    Parameters
    ----------
    position : tuple of float
        The (x, y) coordinates of the circle's center.
    radius : float
        Radius of the ring's centerline (the midpoint between inner and outer edges).
    linewidth : float
        Width of the ring (i.e., the distance from inner to outer edge).
    color : str or tuple
        Fill color of the ring.

    Returns
    -------
    matplotlib.patches.PathPatch
        A patch representing a filled ring (annular circle).

    See Also
    --------
    OutlineCircle : Underlying function used to build the ring.
    RinkCircle : Creates a solid (filled) circle.
    """
    return OutlineCircle(position, radius, linewidth, color)


def ProngedFaceoffCircle(position, radius, linewidth, prong_lengths, prong_linewidth, dist_between_prongs, color):
    """
    Create a four-pronged faceoff circle as used in standard hockey rink layouts.

    This function builds a ring-shaped faceoff circle with four symmetrical prongs
    extending inward from the edge of the circle, spaced evenly along the vertical
    and horizontal axes. The result is a fully composed patch suitable for
    visualizing detailed rink diagrams.

    Parameters
    ----------
    position : tuple of float
        The (x, y) center of the faceoff circle.
    radius : float
        Radius of the ring (centerline).
    thickness : float
        Width of the ring stroke.
    prong_lengths : float
        Length of each prong extending inward from the ring.
    prong_width : float
        Width of each prong.
    dist_between_prongs : float
        Distance between horizontally or vertically opposing prongs (measured between centers).
    color : str or tuple
        Fill color for both the ring and prongs.

    Returns
    -------
    matplotlib.patches.PathPatch
        A patch representing the full pronged faceoff circle, positioned at `position`.

    Notes
    -----
    - Prongs are generated symmetrically around the origin and translated to the target position.
    - The prong geometry assumes flat end caps (`EdgeStyle.FLAT`) for crisp edges.
    - Internally uses `OutlineCircle`, `LinePatch`, `mirror_xy`, and `translate`.

    See Also
    --------
    RinkCircleOutline : Basic circular ring without prongs.
    mirror_xy : Used to create the 4-way symmetry of prongs.
    translate : Used to place the circle at the specified location.
    """
    circle = OutlineCircle((0.0, 0.0), radius, linewidth=linewidth, color=color)
    prong = LinePatch(
        [0.0, 0.0],
        [-linewidth / 2, -(prong_lengths + linewidth / 2)],
        prong_linewidth,
        color=color,
        style=EdgeStyle.FLAT,
    )
    r_prime = radius - linewidth / 2
    xpos = dist_between_prongs / 2
    ypos = -np.sqrt(r_prime**2 - dist_between_prongs**2 / 4.0)
    prong = translate(prong, (xpos, ypos))
    prongs = mirror_xy(prong)
    return translate(union(circle, prongs), position)


def FaceoffCircle(position, radius, thickness, inside_width, color):
    """
    Create a faceoff circle with notches cut out along the horizontal axis.

    This function generates a full rink faceoff circle and subtracts a pair of
    symmetric notches from the inner edge of the ring. The result matches standard
    faceoff circle designs used in ice hockey rinks.

    Parameters
    ----------
    position : tuple of float
        The (x, y) center of the faceoff circle.
    radius : float
        Outer radius of the full circle.
    thickness : float
        Width of the ring stroke (distance from outer edge inward).
    inside_width : float
        Horizontal width of the inner cutout (notch) region.
    color : str or tuple
        Fill color for the ring.

    Returns
    -------
    matplotlib.patches.PathPatch
        A patch representing the faceoff circle with horizontal notches removed.

    Notes
    -----
    - The notch is constructed as a `Sector` and mirrored across the x-axis.
    - The black cutout (`"000000"`) is used as a subtraction geometry and doesn't affect output color.
    - Geometry is centered at (0, 0) and translated to `position`.

    See Also
    --------
    Sector : Used to create the internal notch shape.
    RinkCircle : Full circle with no cutouts.
    difference : Used to subtract notch regions from the outer ring.
    """
    big_circle = RinkCircle((0.0, 0.0), radius, color)
    r_prime = radius - thickness
    theta1 = np.degrees(np.arccos(inside_width / (2 * r_prime)))
    sector = Sector((0.0, 0.0), r_prime, theta1=-theta1, theta2=theta1, color="000000")
    sectors = mirror_x(sector)
    final_shape = translate(difference(big_circle, sectors), position)
    return final_shape  # translate(big_circle, position)


def FaceoffCircleLAccents(position, offset, lengthwise_length, widthwise_length, linewidth, color):
    """
    Create the pair of L-shaped accent marks around a faceoff circle.

    These marks are seen adjacent to the faceoff dot in offensive and defensive zones.
    This function builds one "L" shaped accent and mirrors it across both axes to form
    the standard four-pronged layout, then positions the group at the specified location.

    Parameters
    ----------
    position : tuple of float
        The (x, y) center of the full accent group.
    offset : tuple of float
        Offset from the center to the corner of a single L-mark (relative placement).
    lengthwise_length : float
        Length of the vertical part of the L.
    widthwise_length : float
        Length of the horizontal part of the L.
    linewidth : float
        Thickness of the L-line strokes.
    color : str or tuple
        Fill color for the L-marks.

    Returns
    -------
    matplotlib.patches.PathPatch
        A patch representing the full L-accent set, positioned at `position`.

    Notes
    -----
    - Internally uses `FaceoffCircleLAccent` to define one corner, then mirrors across x and y.
    - L shapes are stroked using `LinePatch`, with flat caps.
    - Geometry is centered at origin before translation.

    See Also
    --------
    FaceoffCircleLAccent : Constructs a single L-shaped accent.
    mirror_xy : Used to generate symmetry.
    translate : Used to move the L-mark group into place.
    """
    one_L = FaceoffCircleLAccent(offset, lengthwise_length, widthwise_length, linewidth, color)
    Ls = mirror_xy(one_L)
    return translate(Ls, position)


def FaceoffCircleLAccent(position, long_length, short_length, linewidth, color):
    """
    Create a single L-shaped faceoff circle accent mark.

    This function builds one "L" shape consisting of a vertical and horizontal line,
    commonly used as markings near faceoff dots. It places the L relative to `position`,
    and applies stroke thickness, direction, and flat caps for consistent styling.

    Parameters
    ----------
    position : tuple of float
        The (x, y) base position of the L's corner (lower-left of the elbow).
    long_length : float
        Length of the vertical segment (the main upright of the L).
    short_length : float
        Length of the horizontal segment (the foot of the L).
    linewidth : float
        Thickness of the lines making up the L.
    color : str or tuple
        Fill color for both segments of the L.

    Returns
    -------
    matplotlib.patches.PathPatch
        A patch representing a single L-shaped accent, translated into position.

    Notes
    -----
    - The L is composed of two perpendicular lines joined at a shared origin.
    - Geometry is translated by a small offset to align with the intended elbow point.
    - Designed to be mirrored to form symmetric markings using `FaceoffCircleLAccents`.

    See Also
    --------
    FaceoffCircleLAccents : Constructs a full mirrored set of L-accents.
    LinePatch : Used to draw each stroke with thickness and cap style.
    union : Combines the two strokes into a single patch.
    translate : Places the shape into rink/world coordinates.
    """

    long_line = LinePatch(
        (0.0, long_length - linewidth / 2),
        (0.0, 0.0),
        linewidth,
        color,
        style=EdgeStyle.FLAT,
    )
    short_line = LinePatch(
        (0.0, 0.0),
        (-linewidth / 2, short_length - linewidth / 2),
        linewidth,
        color,
        style=EdgeStyle.FLAT,
    )
    offset = (position[0] + linewidth / 2, position[1] + linewidth / 2)
    return translate(union(long_line, short_line), offset)


def Trapezoid(position, near_width, far_width, length, linewidth, color):
    """
    Create the trapezoid behind the goal line as a pair of slanted lines.

    This function constructs one side of the goal trapezoid using `LinePatch`
    and mirrors it across the y-axis to form both boundaries. The trapezoid shape
    widens from `near_width` (at the goal line) to `far_width` (at a set distance behind),
    as defined by NHL and IIHF rink standards.

    Parameters
    ----------
    position : tuple of float
        (x, y) offset to position the trapezoid in rink coordinates.
    near_width : float
        Total width of the trapezoid at the goal line (narrow end).
    far_width : float
        Total width of the trapezoid at the back boards (wide end).
    length : float
        Distance from the goal line to the back boards (i.e., trapezoid length).
    linewidth : float
        Thickness of the trapezoid lines.
    color : str or tuple
        Fill color of the trapezoid boundary lines.

    Returns
    -------
    matplotlib.patches.PathPatch
        A patch representing both sides of the trapezoid as mirrored thick lines.

    Notes
    -----
    - The lines are generated based on the slope between near and far ends.
    - Geometry is centered horizontally and placed at `position`.
    - Uses `mirror_y` for symmetry and `translate` for placement.

    See Also
    --------
    LinePatch : Used to create a thick sloped line segment.
    mirror_y : Reflects the left boundary to form the right side.
    translate : Moves the geometry into rink/world coordinates.
    """
    m = (far_width - near_width) / (2 * length)
    line = LinePatch(
        [0.0, length + linewidth], [near_width / 2, near_width / 2 + m * (length + linewidth)], linewidth, color
    )
    lines = translate(mirror_y(line), position)
    return lines


def Net(position, opening_width, corner_radius, max_width, max_depth, color):
    """
    Create a 2D footprint shape of a hockey goal net using a filled polygon and corner arcs.

    The shape is defined relative to the center of the goal line (0, 0) in "goal coordinates".
    The geometry includes:
    - A polygon approximating the frame from post to arc to post,
    - Two semicircular arcs at the rear corners,
    - Symmetry about the centerline,
    - A final translation to `position` in rink/global space.

    Parameters
    ----------
    position : tuple of float
        (x, y) position to translate the entire shape — typically in rink coordinates.
    opening_width : float
        Width of the net opening between the posts (in inches), e.g., 72.0.
    corner_radius : float
        Radius of the curved back corners (in inches), e.g., 18.0.
    max_width : float
        Total outer width of the goal footprint including corner arcs (in inches), e.g., 88.0.
    max_depth : float
        Total depth of the net from goal line to furthest point (in inches), e.g., 44.0.
    color : str
        Color used to fill the shape (e.g., '#0000FF').

    Returns
    -------
    net_shape : Shape
        Composite shape built from a polygon and two mirrored corner circles,
        representing the net's floor layout.

    Notes:
    https://www.dimensions.com/element/ice-hockey-goals#:~:text=Ice%20Hock%20Goals%20are%20constructed,40%E2%80%9D%20(100%20cm)
    """

    def _tangent_point(center, radius, point):
        dx = point[0] - center[0]
        dy = point[1] - center[1]
        center_to_point = (dx**2 + dy**2) ** 0.5
        theta = np.arccos(radius / center_to_point)
        angle = np.arctan2(dy, dx) - theta * np.sign(dy)
        return (center[0] + radius * np.cos(angle), center[1] + radius * np.sin(angle))

    # Intermediate flat dimensions
    flat_width = max_width - 2 * corner_radius
    flat_depth = max_depth - 2 * corner_radius

    # Tangent point between arc and straight side
    arc_center = (flat_depth + corner_radius, flat_width / 2)
    top_post_coord = (0.0, opening_width / 2)
    tangent = _tangent_point(arc_center, radius=corner_radius, point=top_post_coord)

    # Define polygon as a single clean list of (x, y) points
    points = [
        (0.0, 0.0),
        (0.0, opening_width / 2),
        tangent,
        (flat_depth + corner_radius, flat_width / 2 + corner_radius),
        (flat_depth + 2 * corner_radius, flat_width / 2),
        (flat_depth + 2 * corner_radius, -flat_width / 2),
        (flat_depth + corner_radius, -flat_width / 2 - corner_radius),
        (tangent[0], -tangent[1]),
        (0.0, -opening_width / 2),
        (0.0, 0.0),
    ]

    poly = FilledPolygon(points, color=color)
    arc = FilledCircle(center=arc_center, radius=corner_radius, color=color, resolution=12)
    net_shape = union(poly, mirror_y(arc))

    return translate(net_shape, dr=position)


def NetOutline(position, opening_width, corner_radius, max_width, max_depth, linewidth, color):
    mynet = Net(position, opening_width, corner_radius, max_width, max_depth, color)
    return outline(mynet, width=linewidth, color=color, side="outside")


def Posts(position, inside_width, tube_radius, color):
    """
    Create a pair of goal posts as filled circular patches.

    This function generates two circular shapes positioned at the ends of the goal line,
    representing the vertical goal posts. Each post is modeled as a filled circle
    with radius equal to the tube size, and they are symmetrically placed about the center.

    Parameters
    ----------
    position : tuple of float
        (x, y) offset to position the goal post pair in rink coordinates.
    inside_width : float
        Distance between the inside edges of the two posts (goal mouth width).
    tube_radius : float
        Radius of each post's circular cross-section.
    color : str or tuple
        Fill color for the goal post shapes.

    Returns
    -------
    matplotlib.patches.PathPatch
        A patch containing both posts as circular shapes, positioned symmetrically.

    Notes
    -----
    - Posts are centered on the outer edge of the goal frame (outside the goal line).
    - The geometry is mirrored across the y-axis and translated to `position`.

    See Also
    --------
    FilledCircle : Used to create each post.
    mirror_y : Reflects a single post to create its pair.
    translate : Moves the geometry into world coordinates.
    """
    post_circle = FilledCircle((0.0, inside_width / 2 + tube_radius), radius=tube_radius, color=color)
    return translate(mirror_y(post_circle), position)


def CreaseNHL(position, rect_width, rect_height, color, arc_radius=None):
    """
    Create the NHL-style goalie crease as a union of a rectangle and arc.

    This function constructs the standard NHL goalie crease shape — a flat-front
    rectangle combined with a forward-facing semicircular arc. The arc is automatically
    sized to connect smoothly to the rectangle unless an explicit radius is provided.

    Parameters
    ----------
    position : tuple of float
        The (x, y) coordinates to translate the crease into rink/world space.
    rect_width : float
        Total width of the rectangular base of the crease (goal line side).
    rect_height : float
        Height (depth) of the rectangular part of the crease.
    color : str or tuple
        Fill color of the crease.
    arc_radius : float, optional
        Optional radius of the top arc. If not provided, it will be computed to
        smoothly connect the arc to the rectangle's top corners.

    Returns
    -------
    matplotlib.patches.PathPatch
        A patch representing the full NHL crease shape.

    Notes
    -----
    - The arc angle is computed using `arctan(rect_height / (rect_width / 2))`.
    - The entire shape is constructed at the origin and translated to `position`.
    - Designed to align with standard NHL rink markings (e.g. 8’ wide x 4’ deep).

    See Also
    --------
    RectanglePatch : Used for the flat-front rectangular section.
    Wedge : Used for the forward-facing arc.
    union : Merges the arc and rectangle into a single shape.
    translate : Places the crease at the correct rink coordinates.
    """
    if arc_radius is None:
        arc_radius = np.sqrt((rect_width / 2) ** 2 + rect_height**2)

    rectangle = RectanglePatch((-rect_height, -rect_width / 2), rect_height, rect_width, color=color)
    theta1 = np.degrees(np.arctan(rect_height / (rect_width / 2))) + 90
    arc = Wedge((0.0, 0.0), arc_radius, theta1=theta1, theta2=-theta1, color=color)

    crease = union(rectangle, arc)
    return translate(crease, dr=np.array(position))


def CreaseNHLOutline(
    position,
    rect_width,
    accent_height,
    accent_length,
    rect_height,
    color,
    linewidth,
    arc_radius=None,
):
    """
    Create the NHL crease outline, including the stroke and vertical accents.

    This function builds the perimeter outline of the NHL-style goalie crease using
    a stroked union of a rectangular base and a circular arc. It also adds two short
    vertical accent lines on the front corners of the crease, using square caps.

    Parameters
    ----------
    position : tuple of float
        The (x, y) coordinates to translate the crease into rink/world space.
    rect_width : float
        Total width of the rectangular portion of the crease at the goal line.
    accent_height : float
        Distance along the x-axis from center to where the accent lines are placed.
    accent_length : float
        Length of each vertical accent line.
    rect_height : float
        Depth of the rectangular portion of the crease.
    color : str or tuple
        Stroke/fill color for the outline and accents.
    paint_width : float
        Thickness of the crease outline and accent strokes.
    arc_radius : float, optional
        Radius of the arc portion of the crease. If None, it's computed to join the
        rectangle corners smoothly with the arc.

    Returns
    -------
    matplotlib.patches.PathPatch
        A patch representing the full NHL crease outline including the arc,
        rectangle, and vertical accent lines.

    Notes
    -----
    - The arc connects tangentially to the top corners of the rectangle.
    - Vertical accent lines appear at the front corners (goal line side).
    - All components are stroked using `outline` with `EdgeStyle.SQUARE`.

    See Also
    --------
    CreaseNHL : Creates the filled crease shape.
    outline : Used to generate the stroked perimeter of the shape.
    LinePatch : Used for the vertical square-capped accents.
    mirror_y : Reflects one accent to create its pair.
    translate : Moves the shape into final position.
    """
    if arc_radius is None:
        arc_radius = np.sqrt((rect_width / 2) ** 2 + rect_height**2)

    rectangle = RectanglePatch((-rect_height, -rect_width / 2), rect_height, rect_width, color=color)
    theta1 = np.degrees(np.arctan(rect_height / (rect_width / 2))) + 90
    arc = Wedge((0.0, 0.0), arc_radius, theta1=theta1, theta2=-theta1, color=color)

    accent = LinePatch(
        [-accent_height, -accent_height],
        [rect_width / 2, rect_width / 2 - accent_length + linewidth / 2],
        linewidth,
        color,
        EdgeStyle.SQUARE,
    )
    accent = mirror_y(accent)

    crease = union(rectangle, arc)
    crease_outline = outline(crease, width=linewidth, style=EdgeStyle.SQUARE, color=color)
    crease_outline = union(crease_outline, accent)
    return translate(crease_outline, dr=np.array(position))


def CreaseNCAA(
    position,
    radius,
    color,
):
    """
    Create a filled NCAA goalie crease as a semicircular sector and place it on the rink.

    The crease is constructed as a 180° sector centered at the local origin with
    angular span [-90°, 90°] (Matplotlib/PyYAML convention: 0° along +x, CCW positive).
    It is then translated to the provided rink coordinates.

    Parameters
    ----------
    position : array-like of shape (2,)
        (x, y) location of the crease center in rink coordinates (same units as the spec,
        e.g., feet or meters). Typically this is the goal-crease center on the goal line.
    radius : float
        Radius of the semicircular crease. Must be positive and expressed in the same
        units as `position`.
    color : str or tuple
        Fill color for the painted crease. Any Matplotlib-compatible color is accepted
        (e.g., hex string like "#abdbe3", RGBA tuple, named color).

    Returns
    -------
    Shape
        A shape object representing the translated filled crease, compatible with the
        downstream rendering pipeline (e.g., converted to a Matplotlib Patch).

    Notes
    -----
    - Angle convention follows Matplotlib: 0° is the +x axis and angles increase CCW.
    - This function produces the **painted area** of the crease. For the outline/ring
      (stroke) version, see `CreaseOutlineNCAA`.

    Examples
    --------
    >>> crease = CreaseNCAA(position=(89.0, 0.0), radius=6.0, color="#abdbe3")
    >>> rink.add_ice_feature(crease)
    """
    sector = Sector(center=(0.0, 0.0), radius=radius, theta1=270, theta2=90, color=color)
    return translate(sector, dr=np.array(position))


def CreaseOutlineNCAA(
    position,
    radius,
    linewidth,
    color,
):
    """
    Create the painted **outline** (ring/stroke) of the NCAA goalie crease and place it on the rink.

    This constructs the same 180° sector as `CreaseNCAA` and then converts it to an outline
    of the specified paint thickness using square end caps (i.e., squared edges where the
    arc meets the goal line). The result is translated to the provided rink coordinates.

    Parameters
    ----------
    position : array-like of shape (2,)
        (x, y) location of the crease center in rink coordinates (same units as the spec).
    radius : float
        Radius of the semicircular crease. Must be positive and in the same units as `position`.
    paint_width : float
        Thickness of the painted outline (stroke width), in rink units (e.g., feet or meters).
        Must be positive.
    color : str or tuple
        Paint color for the outline. Any Matplotlib-compatible color is accepted.

    Returns
    -------
    Shape
        A shape object representing the translated crease outline, compatible with the
        downstream rendering pipeline (e.g., converted to a Matplotlib Patch).

    See Also
    --------
    CreaseNCAA : Filled (area) version of the NCAA crease.

    Examples
    --------
    >>> crease_outline = CreaseOutlineNCAA(
    ...     position=(89.0, 0.0), radius=6.0, paint_width=0.25, color="#003E7E"
    ... )
    >>> rink.add_ice_feature(crease_outline)
    """
    sector = Sector(center=(0.0, 0.0), radius=radius, theta1=270, theta2=90, color=color)
    sector_outline = outline(sector, width=linewidth, style=EdgeStyle.SQUARE, color=color)
    return translate(sector_outline, dr=np.array(position))


def RinkBox(
    position,
    box_width,
    box_height,
    color,
):
    box = RectanglePatch((-box_width / 2, -box_height / 2), box_width, box_height, color=color)
    return translate(box, dr=np.array(position))


def RinkBoxOutline(
    position,
    box_width,
    box_height,
    linewidth,
    color,
):
    box = RectanglePatch((-box_width / 2, -box_height / 2), box_width, box_height, color=color)
    box_outline = outline(box, width=linewidth, style=EdgeStyle.SQUARE, color=color)
    return translate(box_outline, dr=np.array(position))
