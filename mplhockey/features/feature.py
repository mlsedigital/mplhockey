from .rink_shapes import *
from copy import deepcopy
from mplhockey.geometry.shapes import flip_x, flip_y, flip_xy, scale

map_features = {
    "VLine": VLinePatch,
    "HLine": HLinePatch,
    "RinkCircle": RinkCircle,
    "RinkCircleOutline": RinkCircleOutline,
    "FaceoffCircle": FaceoffCircle,
    "ProngedFaceoffCircle": ProngedFaceoffCircle,
    "FaceoffCircleLAccents": FaceoffCircleLAccents,
    "Trapezoid": Trapezoid,
    "CreaseNHL": CreaseNHL,
    "CreaseNHLOutline": CreaseNHLOutline,
    "CreaseNCAA": CreaseNCAA,
    "CreaseOutlineNCAA": CreaseOutlineNCAA,
    "Posts": Posts,
    "Net": Net,
    "NetOutline": NetOutline,
    "RinkBox": RinkBox,
    "RinkBoxOutline": RinkBoxOutline,
}


def parse_features(feature_list, linewidth=None):
    """
    Parse a list of feature dictionaries into Feature objects.

    Each dictionary in the input list should describe a rink feature, including its
    geometry type, name, and optional symmetry flags. This function looks up the
    corresponding geometry constructor from `map_features`, applies symmetry if needed,
    and returns a list of `Feature` objects ready for drawing or transformation.

    Parameters
    ----------
    feature_list : list of dict
        Each dictionary should contain:
        - "geometry": str, required, must be a key in `map_features`
        - "name": str, optional
        - "mirror": str, optional, one of {"none", "width", "length", "both"}
        - Other keyword arguments are passed to the geometry constructor

    Returns
    -------
    list of Feature
        A list of initialized `Feature` objects.

    Notes
    -----
    - If "geometry" is missing or unrecognized, the feature is skipped.
    - Symmetry options apply automatic mirroring using `mirror_x` and `mirror_y`.
    - Geometry types must be defined in the global `map_features` mapping.

    See Also
    --------
    Feature : Container class for a drawable feature.
    mirror_x, mirror_y : Symmetry operations applied during construction.
    """
    features = []

    for feature in feature_list:
        geometry = feature.pop("geometry", None)
        if geometry is None or geometry not in map_features:
            continue

        FeatureType = map_features[geometry]
        name = feature.pop("name", "unnamed")
        mirror = feature.pop("mirror", "none")

        possible_features = [x for x in feature.keys() if "linewidth" in x]
        if (len(possible_features) > 0) and (linewidth is not None):
            for characteristic in possible_features:
                feature[characteristic] = linewidth

        base_geom = FeatureType(**feature)
        features.append(Feature(name, base_geom))  # original

        if mirror in {"width", "both"}:
            features.append(Feature(f"{name}_mirrored_y", flip_y(deepcopy(base_geom))))
        if mirror in {"length", "both"}:
            features.append(Feature(f"{name}_mirrored_x", flip_x(deepcopy(base_geom))))
        if mirror == "both":
            features.append(Feature(f"{name}_mirrored_xy", flip_xy(deepcopy(base_geom))))

    return features


class Feature:
    """
    A drawable and transformable geometric feature, such as a rink marking or shape.

    This class wraps a single geometric patch (e.g., PathPatch), associates it with a name,
    and optionally applies mirroring for symmetry. It supports transformations, clipping,
    and drawing to a Matplotlib axis.

    Parameters
    ----------
    name : str
        Name of the feature (e.g., "blue_line", "goal_crease").
    geom : matplotlib.patches.Patch
        The geometric patch representing the feature.
    width_symmetric : bool, optional
        If True, the feature is mirrored across the y-axis. Default is False.
    length_symmetric : bool, optional
        If True, the feature is mirrored across the x-axis. Default is False.

    Attributes
    ----------
    name : str
        The feature's name (identifier).
    geom : matplotlib.patches.Patch
        The geometric object, optionally mirrored based on symmetry flags.
    """

    def __init__(self, name, geom):
        self.name = name
        self.geom = deepcopy(geom)

    def copy(self):
        """
        Return a deep copy of the feature.

        Returns
        -------
        Feature
            A new `Feature` instance with the same name and duplicated geometry.
        """
        return Feature(name=self.name, geom=deepcopy(self.geom))

    def crop_to(self, crop_patch):
        """
        Apply a clip path to the feature's geometry.

        Parameters
        ----------
        crop_patch : matplotlib.patches.Patch
            A patch used to define the clipping region.
        """
        self.geom = intersection(self.geom, crop_patch)

    def apply_transform(self, transform):
        """
        Apply an affine transformation to the feature's geometry.

        Parameters
        ----------
        transform : matplotlib.transforms.Affine2D
            An affine transformation (e.g., scale, translate, rotate).
            It is composed with the existing transform on the geometry.
        """
        self.geom.set_transform(transform + self.geom.get_transform())

    def deform(self, func):
        """
        Deform the geometry using a custom vertex transformation function.

        Parameters
        ----------
        func : callable
            A function that takes a (N, 2) NumPy array of vertices and returns
            a deformed array of the same shape.

        Returns
        -------
        matplotlib.patches.PathPatch
            A new deformed patch created from the transformed vertices.

        Notes
        -----
        The original geometry is not mutated.
        """
        return deform(self.geom, func)

    def scale_geometry(self, scale_factor):
        """
        Scale the feature's geometry by a given factor.

        Parameters
        ----------
        scale_factor : float
            The factor by which to scale the geometry.
        """
        self.geom = scale(self.geom, scale_factor, scale_factor)

    def draw(self, ax):
        """
        Add the feature's geometry to the given Matplotlib axis.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The axis to which the feature should be drawn.
        """
        ax.add_patch(self.geom)
