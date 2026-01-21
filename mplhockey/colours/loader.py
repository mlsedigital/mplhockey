from functools import partial
import yaml


def _scheme_constructor(scheme_colours: dict, loader: yaml.SafeLoader, node: yaml.Node):
    key = loader.construct_scalar(node)
    try:
        return scheme_colours[key]
    except KeyError as e:
        raise KeyError(f"Color '{key}' not found in selected scheme") from e


def make_loader_for_scheme(scheme_colors: dict):
    """Return a loader class that resolves !scheme <key> from scheme_colors."""
    L = type("_BoundSchemeLoader", (yaml.SafeLoader,), {})
    yaml.add_constructor("!scheme", partial(_scheme_constructor, scheme_colors), Loader=L)
    return L
