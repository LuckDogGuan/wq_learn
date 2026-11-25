"""Low-complexity economic signal primitives.

The functions deliberately contain no category guessing.  Category and field
semantics are checked by the template registry before an expression is built.
"""


def information_change(field, d=22):
    """New information is incorporated gradually rather than instantaneously."""
    return f"ts_delta({field}, {d})"


def information_acceleration(field, d=22):
    """An accelerating update carries more information than a stable level."""
    return f"ts_delta(ts_delta({field}, {d}), {d})"


def persistent_signal(field, d=66):
    """Persistent fundamentals, holdings or opinions dominate one-off noise."""
    return f"ts_mean({field}, {d})"


def historical_surprise(field, d=66):
    """A field far from its own history represents a fresh economic surprise."""
    return f"ts_zscore({field}, {d})"


def cross_sectional_strength(field):
    """Relative strength across firms is more comparable than raw scale."""
    return f"rank({field})"


def short_horizon_reversal(field, d=5):
    """Short-lived flow, price or sentiment pressure tends to mean-revert."""
    return f"reverse(ts_delta({field}, {d}))"
