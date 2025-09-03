"""Tests for ConnectionTestThread Oracle DB connections"""

import sys
import types
import pytest

pytest.importorskip("PySide6", reason="PySide6 is required for these tests")

from views.dialogs.settings.oracle_connection_dialog import ConnectionTestThread


class DummyCursor:
    def execute(self, _query):
        pass

    def fetchone(self):
        return [1]

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


class DummyConnection:
    def __init__(self, fail_cursor=False):
        self.fail_cursor = fail_cursor
        self.closed = False

    def cursor(self):
        if self.fail_cursor:
            raise Exception("cursor failure")
        return DummyCursor()

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


def make_dummy_oracledb(connect_impl, makedsn_impl=lambda *a, **kw: "dsn"):
    return types.SimpleNamespace(connect=connect_impl, makedsn=makedsn_impl)


def _create_thread(monkeypatch):
    details = {
        "host": "host",
        "port": 1521,
        "username": "user",
        "password": "pass",
        "connection_type": "SID",
        "sid": "sid",
    }
    thread = ConnectionTestThread(details)
    monkeypatch.setattr(thread, "msleep", lambda ms: None)
    monkeypatch.setattr(thread.progress_update, "emit", lambda _msg: None)
    return thread


def test_connection_thread_success(monkeypatch):
    """ConnectionTestThread emits success when DB operations succeed"""
    results = []
    thread = _create_thread(monkeypatch)
    thread.result_ready.emit = lambda success, msg: results.append((success, msg))
    dummy_db = make_dummy_oracledb(lambda **_: DummyConnection())
    monkeypatch.setitem(sys.modules, "oracledb", dummy_db)
    thread.run()
    assert results == [(True, "Connection test successful! Database is accessible.")]


def test_connection_thread_failure(monkeypatch):
    """ConnectionTestThread emits failure when DB connection fails"""
    results = []
    thread = _create_thread(monkeypatch)
    thread.result_ready.emit = lambda success, msg: results.append((success, msg))

    def failing_connect(**_):
        raise Exception("invalid credentials")

    dummy_db = make_dummy_oracledb(failing_connect)
    monkeypatch.setitem(sys.modules, "oracledb", dummy_db)
    thread.run()
    assert results and results[0][0] is False
    assert "invalid credentials" in results[0][1]