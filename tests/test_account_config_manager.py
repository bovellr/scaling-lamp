import sys
from pathlib import Path
from unittest.mock import ANY, MagicMock

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.account_config_manager import AccountConfigManager


def test_account_config_manager(tmp_path, monkeypatch):
    """Exercise AccountConfigManager CRUD operations and events."""
    event_bus = MagicMock()
    config_file = tmp_path / "accounts.json"

    # Patch validation to correct implementation
    def _validate(self, config):
        required = {
            "account_number",
            "transformer",
            "erp_account_code",
            "erp_account_name",
            "currency",
        }
        return required.issubset(config.keys())

    monkeypatch.setattr(AccountConfigManager, "validate_account_config", _validate)

    # Initialize manager; should create file and fire loaded/updated events
    manager = AccountConfigManager(str(config_file), event_bus=event_bus)
    event_bus.publish.assert_any_call("accounts.updated", ANY)
    event_bus.publish.assert_any_call("accounts.loaded", ANY)

    event_bus.publish.reset_mock()

    # Add an account
    new_cfg = {
        "account_number": "87654321",
        "sort_code": "65-43-21",
        "transformer": "standard_uk_bank",
        "erp_account_code": "2002",
        "erp_account_name": "Secondary Bank Account",
        "statement_format": "UK_STANDARD",
        "currency": "GBP",
    }
    assert manager.add_account("Secondary", new_cfg)
    event_bus.publish.assert_called_once_with("accounts.updated", ANY)
    backup_path = config_file.with_suffix(".bak")
    assert backup_path.exists()

    event_bus.publish.reset_mock()

    # Update the account
    updated_cfg = dict(new_cfg)
    updated_cfg["currency"] = "USD"
    assert manager.update_account("Secondary", updated_cfg)
    event_bus.publish.assert_called_once_with("accounts.updated", ANY)

    event_bus.publish.reset_mock()

    # Remove the account
    assert manager.remove_account("Secondary")
    event_bus.publish.assert_called_once_with("accounts.updated", ANY)

    event_bus.publish.reset_mock()

    # Save accounts explicitly
    assert manager.save_accounts(manager.get_accounts())
    event_bus.publish.assert_called_once_with("accounts.updated", ANY)

    event_bus.publish.reset_mock()

    # Reload accounts
    manager.load_accounts()
    event_bus.publish.assert_called_once_with("accounts.loaded", ANY)

    event_bus.publish.reset_mock()

    # Invalid configuration should be rejected
    invalid_cfg = {"account_number": "111"}  # missing required fields
    assert not manager.add_account("Invalid", invalid_cfg)
    assert "Invalid" not in manager.get_accounts()
    event_bus.publish.assert_not_called()

    event_bus.publish.reset_mock()
    assert not manager.update_account("Main Current Account", invalid_cfg)
    event_bus.publish.assert_not_called()
