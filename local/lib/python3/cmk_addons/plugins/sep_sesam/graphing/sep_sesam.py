#!/usr/bin/env python3
"""SEP Sesam Graphing - Metrics, Graphs, and Perfometers."""

from cmk.graphing.v1 import Title
from cmk.graphing.v1.graphs import Graph
from cmk.graphing.v1.metrics import (
    Color,
    DecimalNotation,
    IECNotation,
    Metric,
    Unit,
)
from cmk.graphing.v1.perfometers import Closed, FocusRange, Perfometer


# ---------------------------------------------------------------------------
# Datastore metrics
# ---------------------------------------------------------------------------

metric_sep_sesam_ds_used_percent = Metric(
    name="sep_sesam_ds_used_percent",
    title=Title("Used space"),
    unit=Unit(DecimalNotation("%")),
    color=Color.BLUE,
)

metric_sep_sesam_ds_free_bytes = Metric(
    name="sep_sesam_ds_free_bytes",
    title=Title("Free space"),
    unit=Unit(IECNotation("B")),
    color=Color.GREEN,
)

metric_sep_sesam_ds_used_bytes = Metric(
    name="sep_sesam_ds_used_bytes",
    title=Title("Used space"),
    unit=Unit(IECNotation("B")),
    color=Color.BLUE,
)

metric_sep_sesam_ds_total_bytes = Metric(
    name="sep_sesam_ds_total_bytes",
    title=Title("Total capacity"),
    unit=Unit(IECNotation("B")),
    color=Color.GRAY,
)

# ---------------------------------------------------------------------------
# License metric
# ---------------------------------------------------------------------------

metric_sep_sesam_license_days = Metric(
    name="sep_sesam_license_days",
    title=Title("Days until license expiry"),
    unit=Unit(DecimalNotation("d")),
    color=Color.ORANGE,
)

# ---------------------------------------------------------------------------
# Graphs
# ---------------------------------------------------------------------------

graph_sep_sesam_datastore_space = Graph(
    name="sep_sesam_datastore_space",
    title=Title("SEP Sesam Datastore Space"),
    compound_lines=["sep_sesam_ds_used_bytes"],
    simple_lines=["sep_sesam_ds_total_bytes"],
    optional=["sep_sesam_ds_free_bytes"],
)

# ---------------------------------------------------------------------------
# Perfometers
# ---------------------------------------------------------------------------

perfometer_sep_sesam_datastores = Perfometer(
    name="sep_sesam_datastores",
    focus_range=FocusRange(Closed(0.0), Closed(100.0)),
    segments=["sep_sesam_ds_used_percent"],
)

# ---------------------------------------------------------------------------
# License volume metrics
# ---------------------------------------------------------------------------

metric_sep_sesam_volume_used_pct = Metric(
    name="sep_sesam_volume_used_pct",
    title=Title("License volume used"),
    unit=Unit(DecimalNotation("%")),
    color=Color.ORANGE,
)

perfometer_sep_sesam_license = Perfometer(
    name="sep_sesam_license",
    focus_range=FocusRange(Closed(0.0), Closed(100.0)),
    segments=["sep_sesam_volume_used_pct"],
)
