"""Tests for agent_based/sep_sesam.py."""
import json
import sys
import types
import unittest.mock
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "local/lib/python3"))

# Minimal stubs so we can import sep_sesam without a full CheckMK install
for mod_name in [
    "cmk", "cmk.agent_based", "cmk.agent_based.v2",
]:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = types.ModuleType(mod_name)

# Provide minimal CheckMK stubs
import cmk.agent_based.v2 as cmk_v2
cmk_v2.AgentSection = unittest.mock.MagicMock()
cmk_v2.CheckPlugin = unittest.mock.MagicMock()
class _MockMetric(tuple):
    """Tuple subclass that also supports .get() so tests can iterate mixed results."""
    def get(self, key, default=None):
        return default

cmk_v2.Metric = lambda name, value: _MockMetric((name, value))
cmk_v2.Result = unittest.mock.MagicMock(side_effect=lambda **kw: kw)
cmk_v2.Service = unittest.mock.MagicMock(side_effect=lambda **kw: kw)
cmk_v2.State = types.SimpleNamespace(OK=0, WARN=1, CRIT=2, UNKNOWN=3)
cmk_v2.check_levels = unittest.mock.MagicMock(return_value=[])
cmk_v2.render = types.SimpleNamespace(
    percent=lambda v: f"{v:.2f}%",
    bytes=lambda v: f"{v}B",
    timespan=lambda v: f"{v}s",
)

from cmk_addons.plugins.sep_sesam.agent_based.sep_sesam import (
    discover_sep_sesam_backupjobs,
    check_sep_sesam_backupjobs,
    parse_sep_sesam_backupjobs,
)

from cmk_addons.plugins.sep_sesam.agent_based.sep_sesam import check_sep_sesam_license


class TestBackupJobsDiscover:
    def _section(self, tasks):
        return tasks

    def test_discovers_enabled_tasks(self):
        section = self._section([
            {"name": "task_a", "group": "g1", "resultsSts": "SUCCESSFUL", "exec": True},
            {"name": "task_b", "group": "g1", "resultsSts": "ERROR", "exec": True},
        ])
        services = list(discover_sep_sesam_backupjobs(section))
        items = [s["item"] for s in services]
        assert "task_a" in items
        assert "task_b" in items

    def test_skips_disabled_tasks(self):
        section = self._section([
            {"name": "disabled", "group": "g1", "resultsSts": "SUCCESSFUL", "exec": False},
        ])
        services = list(discover_sep_sesam_backupjobs(section))
        assert len(services) == 0

    def test_empty_section(self):
        assert list(discover_sep_sesam_backupjobs([])) == []

    def test_none_section(self):
        assert list(discover_sep_sesam_backupjobs(None)) == []


class TestBackupJobsCheck:
    def _check(self, item, section):
        return list(check_sep_sesam_backupjobs(item, section))

    def test_successful_is_ok(self):
        section = [{"name": "t1", "group": "g1", "resultsSts": "SUCCESSFUL", "exec": True, "error": None}]
        results = self._check("t1", section)
        assert any(r.get("state") == 0 for r in results)

    def test_warning_is_warn(self):
        section = [{"name": "t1", "group": "g1", "resultsSts": "WARNING", "exec": True, "error": None}]
        results = self._check("t1", section)
        assert any(r.get("state") == 1 for r in results)

    def test_error_is_crit(self):
        section = [{"name": "t1", "group": "g1", "resultsSts": "ERROR", "exec": True, "error": None}]
        results = self._check("t1", section)
        assert any(r.get("state") == 2 for r in results)

    def test_cancelled_is_crit(self):
        section = [{"name": "t1", "group": "g1", "resultsSts": "CANCELLED", "exec": True, "error": None}]
        results = self._check("t1", section)
        assert any(r.get("state") == 2 for r in results)

    def test_unknown_status_is_unknown(self):
        section = [{"name": "t1", "group": "g1", "resultsSts": "SOME_NEW_VALUE", "exec": True, "error": None}]
        results = self._check("t1", section)
        assert any(r.get("state") == 3 for r in results)

    def test_missing_item_is_unknown(self):
        section = [{"name": "other", "group": "g1", "resultsSts": "SUCCESSFUL", "exec": True, "error": None}]
        results = self._check("t1", section)
        assert any(r.get("state") == 3 for r in results)

    def test_error_field_is_crit(self):
        section = [{"name": "t1", "group": "g1", "resultsSts": "ERROR", "exec": True, "error": "HTTP 500"}]
        results = self._check("t1", section)
        assert any(r.get("state") == 2 for r in results)

    def test_summary_contains_status(self):
        section = [{"name": "t1", "group": "g1", "resultsSts": "SUCCESSFUL", "exec": True, "error": None}]
        results = self._check("t1", section)
        assert any("SUCCESSFUL" in str(r.get("summary", "")) for r in results)

    def test_summary_contains_group(self):
        section = [{"name": "t1", "group": "my_group", "resultsSts": "SUCCESSFUL", "exec": True, "error": None}]
        results = self._check("t1", section)
        assert any("my_group" in str(r.get("summary", "")) or "my_group" in str(r.get("details", "")) for r in results)


class TestLicenseCheckEnhanced:
    BASE_PARAMS = {"warn_days": 30, "crit_days": 15}

    def _section(self, **kwargs):
        base = {
            "expiration_date": "2099-12-31",
            "days_remaining": 27000,
            "edition": None,
            "customer": None,
            "volume_used_tb": None,
            "volume_total_tb": None,
            "error": None,
        }
        base.update(kwargs)
        return base

    def test_edition_shown_in_summary(self):
        section = self._section(edition="Ultimate Volume")
        results = list(check_sep_sesam_license(self.BASE_PARAMS, section))
        all_text = " ".join(str(r.get("summary", "")) + str(r.get("details", "")) for r in results)
        assert "Ultimate Volume" in all_text

    def test_customer_shown_in_details(self):
        section = self._section(customer="SEP-AG")
        results = list(check_sep_sesam_license(self.BASE_PARAMS, section))
        all_text = " ".join(str(r.get("summary", "")) + str(r.get("details", "")) for r in results)
        assert "SEP-AG" in all_text

    def test_volume_shown_when_available(self):
        section = self._section(volume_used_tb=1.023, volume_total_tb=21.0)
        results = list(check_sep_sesam_license(self.BASE_PARAMS, section))
        all_text = " ".join(str(r.get("summary", "")) + str(r.get("details", "")) for r in results)
        assert "1.023" in all_text or "TB" in all_text

    def test_none_edition_does_not_crash(self):
        section = self._section(edition=None, customer=None, volume_used_tb=None)
        results = list(check_sep_sesam_license(self.BASE_PARAMS, section))
        assert len(results) > 0

    def test_volume_metric_emitted(self):
        section = self._section(volume_used_tb=1.023, volume_total_tb=21.0)
        results = list(check_sep_sesam_license(self.BASE_PARAMS, section))
        metric_names = [r[0] for r in results if isinstance(r, tuple)]
        assert "sep_sesam_volume_used_pct" in metric_names


from cmk_addons.plugins.sep_sesam.agent_based.sep_sesam import (
    discover_sep_sesam_server_info,
    check_sep_sesam_server_info,
)


class TestServerInfoCheck:
    SAMPLE = {
        "name": "sesam-server",
        "release": "5.2.0.3",
        "kernel": "5.2.0",
        "os": "Linux",
        "dbType": "postgres",
        "javaVersion": "11.0.12",
        "timezone": "Europe/Berlin",
        "error": None,
    }

    def test_discovers_one_service(self):
        services = list(discover_sep_sesam_server_info(self.SAMPLE))
        assert len(services) == 1

    def test_no_discovery_when_none(self):
        assert list(discover_sep_sesam_server_info(None)) == []

    def test_always_ok(self):
        results = list(check_sep_sesam_server_info(self.SAMPLE))
        assert any(r.get("state") == 0 for r in results)

    def test_version_in_summary(self):
        results = list(check_sep_sesam_server_info(self.SAMPLE))
        all_text = " ".join(str(r.get("summary", "")) for r in results)
        assert "5.2.0.3" in all_text

    def test_os_in_summary(self):
        results = list(check_sep_sesam_server_info(self.SAMPLE))
        all_text = " ".join(str(r.get("summary", "")) for r in results)
        assert "Linux" in all_text

    def test_db_type_in_output(self):
        results = list(check_sep_sesam_server_info(self.SAMPLE))
        all_text = " ".join(str(r.get("summary", "")) + str(r.get("details", "")) for r in results)
        assert "postgres" in all_text

    def test_error_is_unknown(self):
        section = {**self.SAMPLE, "error": "HTTP 401"}
        results = list(check_sep_sesam_server_info(section))
        assert any(r.get("state") == 3 for r in results)

    def test_none_fields_dont_crash(self):
        section = {k: None for k in self.SAMPLE}
        section["error"] = None
        results = list(check_sep_sesam_server_info(section))
        assert len(results) > 0
