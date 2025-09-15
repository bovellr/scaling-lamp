"""Configuration package for Bank Reconciliation AI"""

from .settings import AppSettings
from .constants import *
from .legacy_config import load_config

__all__ = ['AppSettings', 'load_config', 'APP_NAME', 'APP_VERSION']
