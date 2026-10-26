"""Meta comparison adapter — stub for nebula package.

The meta comparison adapter is not yet implemented in the nebula package.
It is replaced by the Code skill's meta_compare functions.
"""


def num_adapter(mode="meta_compare", decklist=None, options=None):
    """Meta context adapter.

    Returns PARTIAL status since the adapter is not yet implemented.
    """
    return {
        "adapter": "num_adapter",
        "mode": "meta_compare",
        "status": "UNSUPPORTED",
        "caveat": "Meta comparison adapter not implemented yet",
    }
