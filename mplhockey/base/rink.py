from mplhockey.features.rink_shapes import OuterBoards, IceSurface
from mplhockey.features.feature import Feature, parse_features
from mplhockey.utils import conversion_factor
from mplhockey.geometry import scale
from mplhockey.colours import resolve_colour_theme, make_loader_for_scheme
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d.art3d as art3d
from matplotlib.transforms import Affine2D
import numpy as np
import yaml
import copy


def get_rotated_bounds(xlim, ylim, angle_deg):
    """ """
    # Create 4 corner points of the original view box
    corners = np.array(
        [
            [xlim[0], ylim[0]],
            [xlim[0], ylim[1]],
            [xlim[1], ylim[0]],
            [xlim[1], ylim[1]],
        ]
    )

    # Apply rotation
    transform = Affine2D().rotate_deg_around(0, 0, angle_deg)
    rotated = transform.transform(corners)

    # Get new bounds
    x_vals, y_vals = rotated[:, 0], rotated[:, 1]
    return (x_vals.min(), x_vals.max()), (y_vals.min(), y_vals.max())


class Rink:
    # these are all relative to the rink length/width
    display_ranges_x = {
        "full": (-1.1, 1.1),
        "ozone": (0.2, 1.1),
        "dzone": (-1.1, -0.2),
        "nzone": (-0.4, 0.4),
        "ogoal": (0.6, 1.05),
        "dgoal": (-1.05, -0.6),
    }
    display_ranges_y = {
        "full": (-1.2, 1.2),
        "ozone": (-1.2, 1.2),
        "dzone": (-1.2, 1.2),
        "nzone": (-1.2, 1.2),
        "center": (-1.2, 1.2),
        "ogoal": (-0.7, 0.7),
        "dgoal": (-0.7, 0.7),
    }

    def __init__(
        self,
        width,
        height,
        boards_width,
        corner_radius,
        ice_color,
        boards_color,
        units,
        rotation=0.0,
    ):
        self.units = units
        self.ice_features = {}
        self.other_features = {}
        self.boards = OuterBoards(width, height, boards_width, corner_radius, boards_color)
        self.ice = IceSurface(width, height, corner_radius, ice_color)
        self.display_ranges_x = {k: (v[0] * width / 2, v[1] * width / 2) for k, v in self.display_ranges_x.items()}
        self.display_ranges_y = {k: (v[0] * height / 2, v[1] * height / 2) for k, v in self.display_ranges_y.items()}
        self.rotation = rotation
        self.ax = None

        self.width = width
        self.height = height

    def change_units(self, new_units):
        """
        Change the units of the rink dimensions.
        """
        scale_factor = conversion_factor(self.units, new_units)
        self.units = new_units

        # Scale the boards and ice
        self.boards = scale(self.boards, scale_factor, scale_factor)
        self.ice = scale(self.ice, scale_factor, scale_factor)

        for feature in self.ice_features.values():
            feature.scale_geometry(scale_factor)

        for feature in self.other_features.values():
            feature.scale_geometry(scale_factor)

        # Update display ranges
        self.display_ranges_x = {
            k: (v[0] * scale_factor, v[1] * scale_factor) for k, v in self.display_ranges_x.items()
        }
        self.display_ranges_y = {
            k: (v[0] * scale_factor, v[1] * scale_factor) for k, v in self.display_ranges_y.items()
        }

    def add_ice_feature(self, feature: Feature):
        feature.crop_to(self.ice)
        self.ice_features[feature.name] = feature

    def add_feature(self, feature: Feature):
        self.other_features[feature.name] = feature

    def _gca(self, ax=None, make_3d=False):
        """Gets the current figure and axis. If none is provided, it checks
        if there is currently an active figure and uses that. If not, then it
        creates a new figure/axis pair and returns those.

        Parameters:
        -------
            ax : matplotlib axis (default is none)

        Returns:
        -------
            1) fig : matplotlib figure
            2) ax : matplotlib axis
        """
        if (ax is None) and (self.ax is not None):
            return None, self.ax

        if ax is None:
            if not plt.get_fignums():  # Check if no figure exists
                fig = plt.figure(figsize=(10, 10))  # Create a new figure with specified size
            else:
                fig = plt.gcf()  # Get the current figure

            if not fig.axes:  # Check if there are no axes in the figure
                if make_3d:
                    ax = fig.add_subplot(111, projection="3d")
                    ax.set_axis_off()
                else:
                    ax = fig.add_subplot(111)
            else:
                ax = fig.axes[0]  # Get the first axis if it already exists
        else:
            fig = ax.figure
        self.ax = ax
        return fig, ax

    def draw(self, ax=None, rotation=None, display_range="full", units=None):
        assert (
            display_range in self.display_ranges_x.keys()
        ), f"Invalid display_range '{display_range}', please choose from {list(self.display_ranges_x.keys())}"

        fig, ax = self._gca(ax=ax, make_3d=False)

        if rotation is None:
            rotation = self.rotation

        # Create the transform
        if rotation != 0.0:
            self.rotation = rotation
            rotate = Affine2D().rotate_deg_around(0, 0, rotation)
        else:
            rotate = Affine2D()  # Identity (no-op)

        if units is None:
            scale_factor = 1.0
            scale = Affine2D()
        else:
            scale_factor = conversion_factor(self.units, units)
            scale = Affine2D().scale(scale_factor, scale_factor)

        # Make copies of ice and boards
        ice_copy = copy.copy(self.ice)
        boards_copy = copy.copy(self.boards)
        # Draw base
        ax.add_patch(boards_copy)
        ax.add_patch(ice_copy)
        self._ice_copy = ice_copy
        boards_copy.set_transform(scale + rotate + boards_copy.get_transform())
        ice_copy.set_transform(scale + rotate + ice_copy.get_transform())

        # Draw and crop features
        for feature in self.ice_features.values():
            feature_copy = feature.copy()
            feature_copy.draw(ax)
            feature_copy.apply_transform(scale + rotate)

        # Draw and crop features
        for feature in self.other_features.values():
            feature_copy = feature.copy()
            feature_copy.draw(ax)
            feature_copy.apply_transform(scale + rotate)

        if display_range in self.display_ranges_x.keys():
            xlim = [x * scale_factor for x in self.display_ranges_x[display_range]]
            ylim = [y * scale_factor for y in self.display_ranges_y[display_range]]

        # Rotate bounds if needed
        xlim, ylim = get_rotated_bounds(xlim, ylim, rotation)

        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)

        ax.set_aspect("equal")
        return ax

    def draw3d(self, ax):
        fig, ax = self._gca(ax=ax, make_3d=True)

        ice_copy = copy.copy(self.ice)
        boards_copy = copy.copy(self.boards)

        art3d.pathpatch_2d_to_3d(ice_copy, z=0.0, zdir="z")
        art3d.pathpatch_2d_to_3d(boards_copy, z=-1.0e-2, zdir="z")

        ax.add_patch(boards_copy)
        ax.add_patch(ice_copy)

        for feature in self.ice_features.values():
            feature_copy = feature.copy()
            art3d.pathpatch_2d_to_3d(feature_copy.geom, z=2.0e-2, zdir="z")
            feature_copy.draw(ax)

        return ax

    def _data_transform(self, rotation=None, units=None):
        rot_deg = self.rotation if rotation is None else rotation
        s = 1.0 if units is None else conversion_factor(units, self.units)
        return Affine2D().scale(s, s).rotate_deg_around(0.0, 0.0, rot_deg)

    def transform_xy(self, x, y, rotation=None, units=None):
        T = self._data_transform(rotation=rotation, units=units)
        xy = np.column_stack([np.asarray(x), np.asarray(y)])
        xy_t = T.transform(xy)
        return xy_t[:, 0], xy_t[:, 1]

    def scatter(self, x, y, *args, rotation=None, units=None, ax=None, **kwargs):
        fig, ax = self._gca(ax=ax, make_3d=False)
        x_t, y_t = self.transform_xy(x, y, rotation=rotation, units=units)
        out = ax.scatter(x_t, y_t, *args, **kwargs)
        return out

    def hexbin(self, x, y, *args, rotation=None, units=None, ax=None, **kwargs):
        fig, ax = self._gca(ax=ax, make_3d=False)
        x_t, y_t = self.transform_xy(x, y, rotation=rotation, units=units)
        hb = ax.hexbin(x_t, y_t, *args, **kwargs)

        _ice_copy = getattr(self, "_ice_copy", None)
        if _ice_copy:
            hb.set_clip_path(self._ice_copy)

        return hb

    def plot(self, x, y, *args, rotation=None, units=None, ax=None, **kwargs):
        fig, ax = self._gca(ax=ax, make_3d=False)
        x_t, y_t = self.transform_xy(x, y, rotation=rotation, units=units)
        out = ax.plot(x_t, y_t, *args, **kwargs)
        return out

    @classmethod
    def from_yaml(cls, yaml_file, theme=None, fallback="light", linewidth=None, **kwargs):
        colour_lookup = resolve_colour_theme(theme, fallback=fallback)
        Loader = make_loader_for_scheme(colour_lookup)

        with open(yaml_file, "r") as file:
            config = yaml.load(file, Loader=Loader)
        units = config["specifications"]["units"]

        new_units = kwargs.pop("units", "m")

        rink = cls(units=units, **config["rink"], **kwargs)

        ice_features = parse_features(config["ice_features"], linewidth=linewidth)
        other_features = parse_features(config["other_features"])

        for feature in ice_features:
            rink.add_ice_feature(feature)
        for feature in other_features:
            rink.add_feature(feature)

        rink.change_units(new_units)
        return rink
