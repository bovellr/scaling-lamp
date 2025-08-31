"""Basic tests to verify setup"""

import pytest
import sys
from pathlib import Path

# Skip tests if PySide6 is not available in the environment
pytest.importorskip("PySide6", reason="PySide6 is required for these tests")

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that basic imports work"""
    from config import AppSettings
    from config.constants import APP_NAME, APP_VERSION
    from services import EventBus, setup_logging
    
    assert APP_NAME == "Bank Reconciliation AI"
    assert APP_VERSION == "1.0.0"

def test_settings():
    """Test settings functionality"""
    from config.settings import AppSettings
    
    settings = AppSettings()
    assert hasattr(settings, 'confidence_threshold')
    assert hasattr(settings, 'load_settings')
    assert hasattr(settings, 'save')

def test_event_bus():
    """Test event bus functionality"""
    from services.event_bus import EventBus
    
    event_bus = EventBus()
    
    callback_called = False
    def test_callback():
        nonlocal callback_called
        callback_called = True
    
    event_bus.subscribe('test_event', test_callback)
    event_bus.publish('test_event')
    
    assert callback_called

def test_event_bus_callback_error_propagates():
    """Ensure callback exceptions are not swallowed"""
    from services.event_bus import EventBus

    bus = EventBus()

    def bad_callback():
        raise ValueError("boom")

    bus.subscribe('bad_event', bad_callback)

    with pytest.raises(ValueError):
        bus.publish('bad_event')


def test_settings_save_logs_error(caplog):
    """AppSettings.save should log and propagate errors"""
    from config.settings import AppSettings

    settings = AppSettings()

    class BrokenSettings:
        def setValue(self, *_, **__):
            raise OSError("disk full")

        def sync(self):
            pass

    settings.settings = BrokenSettings()

    with caplog.at_level('ERROR'):
        with pytest.raises(OSError):
            settings.save()

    assert "Failed to save settings" in caplog.text


def test_file_structure():
    """Test that required files exist"""
    required_files = [
        "main.py",
        "config/__init__.py",
        "config/settings.py",
        "config/constants.py",
        "services/__init__.py",
        "services/event_bus.py",
        "services/logging_service.py",
        "views/main_window.py",
        "resources/styles/main.qss"
    ]
    
    for file_path in required_files:
        assert Path(file_path).exists(), f"Required file missing: {file_path}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
