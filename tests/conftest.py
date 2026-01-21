import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib as mpl

mpl.rcParams.update(
    {
        "figure.dpi": 100,
        "savefig.dpi": 100,
        "font.family": "DejaVu Sans",
        "text.usetex": False,
    }
)
