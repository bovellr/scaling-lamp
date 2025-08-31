import logging
import pytest

pytest.importorskip("PySide6", reason="PySide6 is required for these tests")
pytest.importorskip("pandas", reason="pandas is required for these tests")
from PySide6.QtWidgets import QApplication

from views.main_window import MainWindow


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_templates_loaded_once(app, caplog):
    with caplog.at_level(logging.INFO):
        win = MainWindow()
    template_logs = [
        rec for rec in caplog.records if "Loaded" in rec.message and "templates" in rec.message
    ]
    assert len(template_logs) == 1
    win.close()