# CHANGELOG

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-02-25

### Added
- Initial release
- Special agent for SEP Sesam REST API (`agent_sep_sesam`)
- Backup group status monitoring (`sep_sesam_backupgroups`)
- Datastore status and space usage monitoring (`sep_sesam_datastores`)
- License expiration monitoring (`sep_sesam_license`)
- Auto-discovery of backup groups and datastores via API list endpoints
- Configurable used space thresholds for datastores (default: 80%/90%)
- Configurable expiration thresholds for license (default: 30/15 days)
- Performance graphs for datastore space and license days remaining
- Perfometer for datastore used space percentage
- Password passed via stdin for security (not visible in process table)
