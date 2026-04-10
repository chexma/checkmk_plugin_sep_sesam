#!/usr/bin/env python3
"""SEP Sesam Rulesets.

Contains:
- Special Agent ruleset (connection & item configuration)
- Check parameter rulesets for datastores and license
"""

from cmk.rulesets.v1 import Help, Label, Title
from cmk.rulesets.v1.form_specs import (
    BooleanChoice,
    DefaultValue,
    DictElement,
    Dictionary,
    Float,
    Integer,
    LevelDirection,
    List,
    NumberInRange,
    Password,
    SimpleLevels,
    String,
    migrate_to_password,
)
from cmk.rulesets.v1.rule_specs import (
    CheckParameters,
    HostAndItemCondition,
    HostCondition,
    SpecialAgent,
    Topic,
)


# ---------------------------------------------------------------------------
# Special Agent Ruleset
# ---------------------------------------------------------------------------

def _special_agent_formspec():
    return Dictionary(
        title=Title("SEP Sesam Backup Server"),
        help_text=Help(
            "Configure monitoring for SEP Sesam backup software via its REST API. "
            "The special agent connects to the SEP Sesam server and collects status "
            "information for backup groups, datastores, and license."
        ),
        elements={
            "port": DictElement(
                required=False,
                parameter_form=Integer(
                    title=Title("API Port"),
                    help_text=Help(
                        "TCP port of the SEP Sesam REST API. Default: 11401."
                    ),
                    prefill=DefaultValue(11401),
                    custom_validate=[NumberInRange(min_value=1, max_value=65535)],
                ),
            ),
            "username": DictElement(
                required=True,
                parameter_form=String(
                    title=Title("Username"),
                    help_text=Help("SEP Sesam API username for authentication."),
                ),
            ),
            "password": DictElement(
                required=True,
                parameter_form=Password(
                    title=Title("Password"),
                    help_text=Help("SEP Sesam API password for authentication."),
                    migrate=migrate_to_password,
                ),
            ),
            "verify_ssl": DictElement(
                required=False,
                parameter_form=BooleanChoice(
                    title=Title("Verify SSL certificate"),
                    help_text=Help(
                        "Disable SSL verification only if the server uses a "
                        "self-signed certificate."
                    ),
                    prefill=DefaultValue(True),
                    label=Label("Verify SSL certificate"),
                ),
            ),
            "timeout": DictElement(
                required=False,
                parameter_form=Integer(
                    title=Title("Connection timeout"),
                    help_text=Help(
                        "Maximum time in seconds to wait for an API response."
                    ),
                    prefill=DefaultValue(30),
                    custom_validate=[NumberInRange(min_value=1, max_value=300)],
                ),
            ),
            "backupgroups": DictElement(
                required=False,
                parameter_form=List(
                    title=Title("Backup Groups"),
                    help_text=Help(
                        "Names of backup groups to monitor. "
                        "Leave empty to auto-discover all available groups."
                    ),
                    element_template=String(
                        title=Title("Backup Group Name"),
                    ),
                ),
            ),
            "datastores": DictElement(
                required=False,
                parameter_form=List(
                    title=Title("Datastores"),
                    help_text=Help(
                        "Names of datastores to monitor. "
                        "Leave empty to auto-discover all available datastores."
                    ),
                    element_template=String(
                        title=Title("Datastore Name"),
                    ),
                ),
            ),
        },
    )


rule_spec_sep_sesam = SpecialAgent(
    name="sep_sesam",
    title=Title("SEP Sesam Backup Server"),
    topic=Topic.STORAGE,
    parameter_form=_special_agent_formspec,
)


# ---------------------------------------------------------------------------
# Check Parameter Ruleset: Datastores
# ---------------------------------------------------------------------------

def _datastore_parameter_form():
    return Dictionary(
        title=Title("SEP Sesam Datastore Usage"),
        elements={
            "used_levels": DictElement(
                required=True,
                parameter_form=SimpleLevels(
                    title=Title("Used space levels"),
                    help_text=Help(
                        "Warning and critical thresholds for datastore usage "
                        "as a percentage of total capacity."
                    ),
                    form_spec_template=Float(unit_symbol="%"),
                    level_direction=LevelDirection.UPPER,
                    prefill_fixed_levels=DefaultValue(value=(80.0, 90.0)),
                ),
            ),
        },
    )


rule_spec_sep_sesam_datastores = CheckParameters(
    name="sep_sesam_datastores",
    title=Title("SEP Sesam Datastore Usage"),
    topic=Topic.STORAGE,
    parameter_form=_datastore_parameter_form,
    condition=HostAndItemCondition(
        item_title=Title("Datastore name"),
    ),
)


# ---------------------------------------------------------------------------
# Check Parameter Ruleset: License
# ---------------------------------------------------------------------------

def _license_parameter_form():
    return Dictionary(
        title=Title("SEP Sesam License Expiry"),
        elements={
            "warn_days": DictElement(
                required=True,
                parameter_form=Integer(
                    title=Title("Warning threshold (days)"),
                    help_text=Help(
                        "Trigger WARNING when the license expires within this "
                        "many days."
                    ),
                    prefill=DefaultValue(30),
                    custom_validate=[NumberInRange(min_value=1)],
                ),
            ),
            "crit_days": DictElement(
                required=True,
                parameter_form=Integer(
                    title=Title("Critical threshold (days)"),
                    help_text=Help(
                        "Trigger CRITICAL when the license expires within this "
                        "many days."
                    ),
                    prefill=DefaultValue(15),
                    custom_validate=[NumberInRange(min_value=0)],
                ),
            ),
        },
    )


rule_spec_sep_sesam_license = CheckParameters(
    name="sep_sesam_license",
    title=Title("SEP Sesam License Expiry"),
    topic=Topic.STORAGE,
    parameter_form=_license_parameter_form,
    condition=HostCondition(),
)
