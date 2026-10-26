"""Commander Spellbook adapter — stub for nebula package.

The commander spellbook adapter is not yet implemented in the nebula
package. It is replaced by the Code skill's spellbook_find_decklist_combos
and spellbook_combo_details functions.
"""


def num_adapter(mode="commander_spellbook", decklist=None, options=None):
    """Commander Spellbook combos adapter.

    Returns PARTIAL status since the adapter is not yet implemented.
    """
    return {
        "adapter": "num_adapter",
        "mode": "commander_spellbook",
        "status": "UNSUPPORTED",
        "caveat": "Commander spellbook adapter not implemented yet",
    }
