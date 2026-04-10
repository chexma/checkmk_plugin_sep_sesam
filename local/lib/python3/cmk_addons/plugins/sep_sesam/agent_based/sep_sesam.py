#!/usr/bin/env python3
"""CheckMK Check Plugins for SEP Sesam Backup Software.

Provides five check plugins:
- sep_sesam_backupgroups:  Status of individual backup groups
- sep_sesam_backupjobs:    Status of individual backup tasks
- sep_sesam_datastores:    Status and space usage of datastores
- sep_sesam_license:       License expiration, edition, customer, volume
- sep_sesam_server_info:   Server version, OS, database type (informational)
"""

import json
import re
from typing import Any, Optional

from cmk.agent_based.v2 import (
    AgentSection,
    CheckPlugin,
    Metric,
    Result,
    Service,
    State,
    check_levels,
    render,
)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _parse_size_to_bytes(size_str: Any) -> Optional[int]:
    """Convert a size string like '100GB' or '1.5TB' into bytes.

    Returns None if the value cannot be parsed.
    """
    if size_str is None or size_str == "":
        return None
    s = str(size_str).strip()
    # Plain integer → already bytes
    try:
        return int(s)
    except ValueError:
        pass
    units = {
        "B": 1,
        "KB": 1024,
        "MB": 1024 ** 2,
        "GB": 1024 ** 3,
        "TB": 1024 ** 4,
        "PB": 1024 ** 5,
    }
    match = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*([A-Z]+)$", s.upper())
    if match:
        value = float(match.group(1))
        unit = match.group(2)
        return int(value * units.get(unit, 1))
    return None


def _parse_json_section(string_table):
    """Parse a single-line JSON agent section."""
    if not string_table:
        return None
    try:
        return json.loads(string_table[0][0])
    except (json.JSONDecodeError, IndexError):
        return None


# ---------------------------------------------------------------------------
# Backup Groups
# ---------------------------------------------------------------------------

def parse_sep_sesam_backupgroups(string_table):
    return _parse_json_section(string_table)


def discover_sep_sesam_backupgroups(section):
    if not section:
        return
    for group in section:
        if isinstance(group, dict) and "name" in group:
            yield Service(item=group["name"])


def check_sep_sesam_backupgroups(item, section):
    if not section:
        yield Result(state=State.UNKNOWN, summary="No data received from agent")
        return

    group_data = next(
        (g for g in section if isinstance(g, dict) and g.get("name") == item), None
    )
    if group_data is None:
        yield Result(
            state=State.UNKNOWN,
            summary=f"Backup group '{item}' not found in agent output",
        )
        return

    error = group_data.get("error")
    if error:
        yield Result(state=State.CRIT, summary=f"Error fetching data: {error}")
        return

    status = group_data.get("resultsSts", "UNKNOWN")
    state_map = {
        "SUCCESSFUL": State.OK,
        "WARNING": State.WARN,
        "ERROR": State.CRIT,
        "CANCELLED": State.CRIT,
    }
    state = state_map.get(status, State.UNKNOWN)
    yield Result(state=state, summary=f"Status: {status}")


agent_section_sep_sesam_backupgroups = AgentSection(
    name="sep_sesam_backupgroups",
    parse_function=parse_sep_sesam_backupgroups,
)

check_plugin_sep_sesam_backupgroups = CheckPlugin(
    name="sep_sesam_backupgroups",
    service_name="SEP Sesam Backup Group %s",
    discovery_function=discover_sep_sesam_backupgroups,
    check_function=check_sep_sesam_backupgroups,
)


# ---------------------------------------------------------------------------
# Backup Jobs (individual tasks)
# ---------------------------------------------------------------------------

def parse_sep_sesam_backupjobs(string_table):
    return _parse_json_section(string_table)


def discover_sep_sesam_backupjobs(section):
    if not section:
        return
    for task in section:
        if isinstance(task, dict) and task.get("name") and task.get("exec", True):
            yield Service(item=task["name"])


def check_sep_sesam_backupjobs(item, section):
    if not section:
        yield Result(state=State.UNKNOWN, summary="No data received from agent")
        return

    task_data = next(
        (t for t in section if isinstance(t, dict) and t.get("name") == item), None
    )
    if task_data is None:
        yield Result(
            state=State.UNKNOWN,
            summary=f"Backup job '{item}' not found in agent output",
        )
        return

    error = task_data.get("error")
    if error:
        yield Result(state=State.CRIT, summary=f"Error fetching data: {error}")
        return

    status = task_data.get("resultsSts", "UNKNOWN")
    group = task_data.get("group", "")
    state_map = {
        "SUCCESSFUL": State.OK,
        "WARNING": State.WARN,
        "ERROR": State.CRIT,
        "CANCELLED": State.CRIT,
    }
    state = state_map.get(status, State.UNKNOWN)
    group_info = f" (Group: {group})" if group else ""
    yield Result(state=state, summary=f"Status: {status}{group_info}")


agent_section_sep_sesam_backupjobs = AgentSection(
    name="sep_sesam_backupjobs",
    parse_function=parse_sep_sesam_backupjobs,
)

check_plugin_sep_sesam_backupjobs = CheckPlugin(
    name="sep_sesam_backupjobs",
    service_name="SEP Sesam Backup Job %s",
    discovery_function=discover_sep_sesam_backupjobs,
    check_function=check_sep_sesam_backupjobs,
)


# ---------------------------------------------------------------------------
# Datastores
# ---------------------------------------------------------------------------

def parse_sep_sesam_datastores(string_table):
    return _parse_json_section(string_table)


def discover_sep_sesam_datastores(section):
    if not section:
        return
    for ds in section:
        if isinstance(ds, dict) and "name" in ds:
            yield Service(item=ds["name"])


def check_sep_sesam_datastores(item, params, section):
    if not section:
        yield Result(state=State.UNKNOWN, summary="No data received from agent")
        return

    ds_data = next(
        (d for d in section if isinstance(d, dict) and d.get("name") == item), None
    )
    if ds_data is None:
        yield Result(
            state=State.UNKNOWN,
            summary=f"Datastore '{item}' not found in agent output",
        )
        return

    error = ds_data.get("error")
    if error:
        yield Result(state=State.CRIT, summary=f"Error fetching data: {error}")
        return

    # Map SEP Sesam status codes to CheckMK states
    raw_status = str(ds_data.get("status", "UNKNOWN"))
    status_map = {
        "0": (State.OK, "OK"),
        "1": (State.WARN, "Warning"),
        "8": (State.CRIT, "Critical"),
    }
    state, status_text = status_map.get(
        raw_status, (State.UNKNOWN, f"Unknown (code: {raw_status})")
    )
    yield Result(state=state, summary=f"Status: {status_text}")

    # Space metrics
    free_bytes = _parse_size_to_bytes(ds_data.get("free", "0"))
    used_bytes = _parse_size_to_bytes(ds_data.get("used", "0"))
    total_bytes = _parse_size_to_bytes(ds_data.get("total", "0"))

    if total_bytes and total_bytes > 0:
        used_pct = (used_bytes or 0) / total_bytes * 100.0
        yield from check_levels(
            used_pct,
            levels_upper=params.get("used_levels"),
            metric_name="sep_sesam_ds_used_percent",
            label="Used",
            render_func=render.percent,
        )
        yield Result(
            state=State.OK,
            notice=(
                f"Free: {render.bytes(free_bytes or 0)}, "
                f"Used: {render.bytes(used_bytes or 0)}, "
                f"Total: {render.bytes(total_bytes)}"
            ),
        )
        if free_bytes is not None:
            yield Metric("sep_sesam_ds_free_bytes", free_bytes)
        if used_bytes is not None:
            yield Metric("sep_sesam_ds_used_bytes", used_bytes)
        yield Metric("sep_sesam_ds_total_bytes", total_bytes)


agent_section_sep_sesam_datastores = AgentSection(
    name="sep_sesam_datastores",
    parse_function=parse_sep_sesam_datastores,
)

check_plugin_sep_sesam_datastores = CheckPlugin(
    name="sep_sesam_datastores",
    service_name="SEP Sesam Datastore %s",
    discovery_function=discover_sep_sesam_datastores,
    check_function=check_sep_sesam_datastores,
    check_default_parameters={
        "used_levels": ("fixed", (80.0, 90.0)),
    },
    check_ruleset_name="sep_sesam_datastores",
)


# ---------------------------------------------------------------------------
# License
# ---------------------------------------------------------------------------

def parse_sep_sesam_license(string_table):
    return _parse_json_section(string_table)


def discover_sep_sesam_license(section):
    if section is not None:
        yield Service()


def check_sep_sesam_license(params, section):
    if section is None:
        yield Result(state=State.UNKNOWN, summary="No data received from agent")
        return

    error = section.get("error")
    if error:
        yield Result(state=State.CRIT, summary=f"Error fetching license data: {error}")
        return

    expiration_date = section.get("expiration_date")
    days_remaining = section.get("days_remaining")
    edition = section.get("edition")
    customer = section.get("customer")
    volume_used_tb = section.get("volume_used_tb")
    volume_total_tb = section.get("volume_total_tb")

    if expiration_date is None or days_remaining is None:
        yield Result(state=State.UNKNOWN, summary="License expiration date unavailable")
        return

    warn_days = params.get("warn_days", 30)
    crit_days = params.get("crit_days", 15)

    edition_str = f" | Edition: {edition}" if edition else ""

    if days_remaining <= 0:
        state = State.CRIT
        summary = (
            f"License EXPIRED on {expiration_date} "
            f"({abs(days_remaining)} days ago){edition_str}"
        )
    elif days_remaining <= crit_days:
        state = State.CRIT
        summary = (
            f"License expires {expiration_date} "
            f"({days_remaining} days remaining){edition_str}"
        )
    elif days_remaining <= warn_days:
        state = State.WARN
        summary = (
            f"License expires {expiration_date} "
            f"({days_remaining} days remaining){edition_str}"
        )
    else:
        state = State.OK
        summary = (
            f"License valid until {expiration_date} "
            f"({days_remaining} days remaining){edition_str}"
        )

    yield Result(state=state, summary=summary)
    yield Metric("sep_sesam_license_days", days_remaining)

    # Additional details
    details_parts = []
    if customer:
        details_parts.append(f"Customer: {customer}")
    if volume_used_tb is not None and volume_total_tb is not None:
        details_parts.append(f"Volume: {volume_used_tb:.3f} TB of {volume_total_tb:.0f} TB")
        if volume_total_tb > 0:
            vol_pct = volume_used_tb / volume_total_tb * 100.0
            yield Metric("sep_sesam_volume_used_pct", vol_pct)

    if details_parts:
        yield Result(state=State.OK, notice=" | ".join(details_parts))


agent_section_sep_sesam_license = AgentSection(
    name="sep_sesam_license",
    parse_function=parse_sep_sesam_license,
)

check_plugin_sep_sesam_license = CheckPlugin(
    name="sep_sesam_license",
    service_name="SEP Sesam License",
    discovery_function=discover_sep_sesam_license,
    check_function=check_sep_sesam_license,
    check_default_parameters={
        "warn_days": 30,
        "crit_days": 15,
    },
    check_ruleset_name="sep_sesam_license",
)


# ---------------------------------------------------------------------------
# Server Info
# ---------------------------------------------------------------------------

def parse_sep_sesam_server_info(string_table):
    return _parse_json_section(string_table)


def discover_sep_sesam_server_info(section):
    if section is not None:
        yield Service()


def check_sep_sesam_server_info(section):
    if section is None:
        yield Result(state=State.UNKNOWN, summary="No data received from agent")
        return

    error = section.get("error")
    if error:
        yield Result(state=State.UNKNOWN, summary=f"Error fetching server info: {error}")
        return

    release = section.get("release") or "unknown"
    os_name = section.get("os") or "unknown"
    db_type = section.get("dbType") or "unknown"
    java = section.get("javaVersion")
    timezone = section.get("timezone")
    kernel = section.get("kernel")

    summary = f"Version: {release}, OS: {os_name}, DB: {db_type}"
    yield Result(state=State.OK, summary=summary)

    details_parts = []
    if kernel:
        details_parts.append(f"Kernel: {kernel}")
    if java:
        details_parts.append(f"Java: {java}")
    if timezone:
        details_parts.append(f"Timezone: {timezone}")
    if details_parts:
        yield Result(state=State.OK, notice=" | ".join(details_parts))


agent_section_sep_sesam_server_info = AgentSection(
    name="sep_sesam_server_info",
    parse_function=parse_sep_sesam_server_info,
)

check_plugin_sep_sesam_server_info = CheckPlugin(
    name="sep_sesam_server_info",
    service_name="SEP Sesam Server",
    discovery_function=discover_sep_sesam_server_info,
    check_function=check_sep_sesam_server_info,
)
