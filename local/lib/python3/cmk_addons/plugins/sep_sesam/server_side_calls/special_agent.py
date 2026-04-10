#!/usr/bin/env python3
"""SEP Sesam Special Agent - Server Side Calls Configuration.

Maps GUI ruleset parameters to CLI arguments for the agent_sep_sesam executable.
The password is passed via stdin for security (not visible in process table).
"""

from cmk.server_side_calls.v1 import (
    SpecialAgentCommand,
    SpecialAgentConfig,
    noop_parser,
)


def _agent_arguments(params, host_config):
    args = [
        "--hostname", host_config.primary_ip_config.address,
    ]

    if "port" in params:
        args.extend(["--port", str(params["port"])])

    if "username" in params:
        args.extend(["--username", params["username"]])

    if not params.get("verify_ssl", True):
        args.append("--no-verify-ssl")

    if "timeout" in params:
        args.extend(["--timeout", str(params["timeout"])])

    backupgroups = params.get("backupgroups") or []
    if backupgroups:
        args.append("--backupgroups")
        args.extend(backupgroups)

    datastores = params.get("datastores") or []
    if datastores:
        args.append("--datastores")
        args.extend(datastores)

    # Pass password via stdin – keeps it out of the process table
    password = params["password"].unsafe() if "password" in params else ""

    yield SpecialAgentCommand(
        command_arguments=args,
        stdin=password,
    )


special_agent_sep_sesam = SpecialAgentConfig(
    name="sep_sesam",
    parameter_parser=noop_parser,
    commands_function=_agent_arguments,
)
