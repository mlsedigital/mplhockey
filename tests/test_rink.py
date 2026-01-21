import pytest
import numpy as np
from mplhockey.rink import NHLRink, KHLRink, NCAARink, IIHFRink, PWHLRink, NRLRink, Rink
from matplotlib.colors import LinearSegmentedColormap, Normalize
import matplotlib.pyplot as plt


@pytest.mark.mpl_image_compare(baseline_dir="baseline", tolerance=10)
def test_rink_render():
    rink = NHLRink()
    fig, ax = plt.subplots(dpi=100, figsize=(10, 6))
    rink.draw(ax, rotation=0.0)
    return fig


@pytest.mark.mpl_image_compare(baseline_dir="baseline", tolerance=10)
def test_rink():
    # Load your rink from YAML
    nhl = Rink.from_yaml("mplhockey/rink_dims/nhl.yaml", linewidth=2)

    # Set up a 3D plot with better framing
    fig = plt.figure(figsize=(10, 6), dpi=100)
    ax = fig.add_subplot(111, projection="3d", computed_zorder=False)

    # --- Perspective (projective) projection ---
    ax.set_proj_type("persp")

    # Draw the rink in 3D
    nhl.draw3d(ax)

    # Camera
    ax.view_init(elev=-30, azim=240)

    # Hard limits
    ax.set_xlim(-15, 15)
    ax.set_ylim(-15, 15)
    ax.set_zlim(-1, 1)

    # Aspect
    ax.set_box_aspect([1, 1, 2])

    # Remove axes + grid
    ax.set_axis_off()
    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])

    # Kill padding around the axes area
    ax.margins(x=0, y=0, z=0)
    ax.set_position([0, 0, 1, 1])
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)

    return fig


@pytest.mark.mpl_image_compare(baseline_dir="baseline", tolerance=10)
def test_nhl_3d():
    # Load the NHL rink
    nhl = Rink.from_yaml("mplhockey/rink_dims/nhl.yaml")

    fig = plt.figure(figsize=(10, 6), dpi=100)
    ax = fig.add_subplot(111, projection="3d", computed_zorder=False)

    # Draw rink FIRST
    nhl.draw3d(ax)

    # Camera
    ax.view_init(elev=30, azim=240)

    # Hard limits
    ax.set_xlim(-15, 15)
    ax.set_ylim(-15, 15)
    ax.set_zlim(-1, 1)

    # Aspect
    ax.set_box_aspect([1, 1, 2])

    # Remove axes + grid
    ax.set_axis_off()
    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])

    ax.margins(x=0, y=0, z=0)
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)

    return fig


@pytest.mark.mpl_image_compare(baseline_dir="baseline", tolerance=10)
def test_hexbin_overlay_rotation():
    rng = np.random.default_rng(12345)

    rink = NHLRink(fallback="over-dark", linewidth=1)

    fig, ax = plt.subplots(figsize=(20, 6), dpi=150)

    # --- Deterministic synthetic data in rink coords (centered at 0,0) ---
    n_pts = 20000
    x1 = rng.uniform(-rink.width / 2, 0.0, size=n_pts)
    y1 = rng.uniform(-rink.height / 2, rink.height / 2, size=n_pts)

    x2 = rng.uniform(0.0, rink.width / 2, size=n_pts)
    y2 = rng.uniform(-rink.height / 2, rink.height / 2, size=n_pts)

    # --- Draw rink ON TOP ---
    rotation = 20  # degrees
    rink.draw(ax=ax, rotation=rotation, display_range="full")

    # --- Draw hexbins FIRST (behind rink); rink.hexbin should handle rotation/transform ---
    rink.hexbin(
        x1,
        y1,
        gridsize=(30, 15),
        mincnt=1,
        linewidths=0,
        zorder=0,
    )

    rink.hexbin(
        x2,
        y2,
        gridsize=(30, 15),
        mincnt=1,
        linewidths=0,
        cmap="hot",
        zorder=0,
    )

    # --- Match your visual style ---
    ax.set_facecolor("#202020")
    ax.set_axis_off()
    fig.tight_layout(pad=0)

    return fig


@pytest.mark.mpl_image_compare(baseline_dir="baseline", tolerance=10)
def test_rotation_units_mosaic():
    fig, axs = plt.subplot_mosaic(
        "AB",
        figsize=(8, 4),
        sharex=False,
        sharey=False,
    )

    rinkA = NHLRink(theme="light")
    rinkB = NHLRink(theme="light")

    # Same rotation, different display ranges + units
    rinkA.draw(ax=axs["A"], units="m", display_range="ozone", rotation=45)
    rinkB.draw(ax=axs["B"], units="ft", display_range="full", rotation=45)

    # Cross-unit plotting on top (these lines are the “proof” bits)
    rinkB.plot([0, 0], [-10, 10], color="g", units="km")
    rinkA.plot([-10, 10], [0, 0])

    # Clean look + deterministic layout
    for k in ("A", "B"):
        axs[k].set_axis_off()

    fig.tight_layout(pad=0)
    return fig


@pytest.mark.mpl_image_compare(baseline_dir="baseline", tolerance=10)
def test_khl_rink():
    rink = KHLRink(units="m", rotation=90)
    fig, ax = plt.subplots(dpi=100, figsize=(10, 6))
    rink.draw(ax, display_range="ozone")
    return fig


@pytest.mark.mpl_image_compare(baseline_dir="baseline", tolerance=10)
def test_ncaa_rink():
    rink = NCAARink()
    fig, ax = plt.subplots(dpi=100, figsize=(10, 6))
    rink.draw(ax, display_range="ozone")
    return fig


@pytest.mark.mpl_image_compare(baseline_dir="baseline", tolerance=10)
def test_iihf_rink():
    rink = IIHFRink()
    fig, ax = plt.subplots(dpi=100, figsize=(10, 6))
    rink.draw(ax, display_range="dzone")
    return fig


@pytest.mark.mpl_image_compare(baseline_dir="baseline", tolerance=10)
def test_pwhl_rink():
    rink = PWHLRink()
    fig, ax = plt.subplots(dpi=100, figsize=(10, 6))
    rink.draw(ax, display_range="ozone")
    return fig


@pytest.mark.mpl_image_compare(baseline_dir="baseline", tolerance=10)
def test_pwhl_rink():
    rink = NRLRink(units="m", rotation=120)
    fig, ax = plt.subplots(dpi=100, figsize=(10, 6))
    rink.draw(ax, display_range="full")
    return fig


@pytest.mark.mpl_image_compare(baseline_dir="baseline", tolerance=10)
def test_ringette_rink():
    rink = NRLRink(theme="over-dark", linewidth=1)

    fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
    # Draw rink on top
    rink.draw(ax=ax)

    # Seeded RNG = deterministic bins
    rng = np.random.default_rng(1234)
    n_pts = 20000

    x1 = rng.uniform(-rink.width / 2, 0.0, size=n_pts)
    y1 = rng.uniform(-rink.height / 2, rink.height / 2, size=n_pts)
    x2 = rng.uniform(0.0, rink.width / 2, size=n_pts)
    y2 = rng.uniform(-rink.height / 2, rink.height / 2, size=n_pts)

    ice_cmap = LinearSegmentedColormap.from_list(
        "ice",
        ["#0b1c2d", "#1e4b6b", "#4fa3d1", "#cce9f7"],
        N=256,
    )

    # Draw hexbins first (behind)
    hb1 = rink.hexbin(x1, y1, gridsize=(30, 15), mincnt=1, linewidths=0, cmap=ice_cmap, alpha=0.9, zorder=0)
    hb2 = rink.hexbin(x2, y2, gridsize=(30, 15), mincnt=1, linewidths=0, cmap=ice_cmap, alpha=0.9, zorder=0)

    # Shared normalization for both halves (stabilizes color scaling)
    vmax = float(max(hb1.get_array().max(), hb2.get_array().max()))
    norm = Normalize(vmin=1, vmax=vmax if vmax > 1 else 1)
    hb1.set_norm(norm)
    hb2.set_norm(norm)

    ax.set_axis_off()

    return fig
