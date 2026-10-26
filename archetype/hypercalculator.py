"""Hypercalculator adapter — stub for nebula package.

The hypercalculator adapter is not yet implemented in the nebula package.
It is replaced by the Code skill's hypercalculator functions.
"""


def num_adapter(mode="hypercalculator", decklist=None, options=None):
    """Hypercalculator probabilities adapter.

    Returns PARTIAL status since the adapter is not yet implemented.
    """
    return {
        "adapter": "num_adapter",
        "mode": "hypercalculator",
        "status": "UNSUPPORTED",
        "caveat": "Hypercalculator adapter not implemented yet",
    }
