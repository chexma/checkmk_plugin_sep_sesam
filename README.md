# SEP Sesam Backup Monitoring Plugin for Checkmk

Checkmk 2.4 plugin for monitoring SEP Sesam backup software via the REST API.

## Features

- **Backup Groups** - Status monitoring (SUCCESSFUL / WARNING / ERROR / CANCELLED)
- **Datastores** - Operational status and space usage with configurable thresholds
- **License** - Maintenance expiration monitoring with configurable warn/critical thresholds

## Services Created

| Service | Description |
|---------|-------------|
| SEP Sesam Backup Group {name} | Backup group result status |
| SEP Sesam Datastore {name} | Datastore status and space usage |
| SEP Sesam License | Maintenance license expiration date |

## Rulesets

| Ruleset | Service | Parameters |
|---------|---------|------------|
| SEP Sesam Backup Server | (Special Agent) | Connection settings, groups/datastores to monitor |
| SEP Sesam Datastore Usage | SEP Sesam Datastore * | Used space warn/crit thresholds (%) |
| SEP Sesam License Expiry | SEP Sesam License | Expiration warn/crit thresholds (days) |

## Requirements

- Checkmk 2.4.0p1 or later
- SEP Sesam server with REST API enabled (default port: 11401)
- SEP Sesam user account with API access

## License

GPLv2
