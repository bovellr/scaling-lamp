# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.
# models/database.py
"""
Data persistence layer for templates and audit trails.
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Optional
from dataclasses import asdict
from datetime import datetime
from .data_models import BankTemplate, ReconciliationReport
import logging

logger = logging.getLogger(__name__)

class TemplateRepository:
    """Repository for managing bank templates."""
    
    def __init__(self, templates_file: str = "data/bank_templates.json"):
        self.templates_file = Path(templates_file)
        self.templates_file.parent.mkdir(exist_ok=True)
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create templates file if it doesn't exist."""
        if not self.templates_file.exists():
            self._save_templates([])
    
    def _load_templates(self) -> List[dict]:
        """Load templates from file."""
        try:
            with open(self.templates_file, 'r') as f:
                data = json.load(f)
                return data.get('templates', [])
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
            return []
    
    def _save_templates(self, templates: List[dict]):
        """Save templates to file."""
        try:
            data = {'templates': templates}
            with open(self.templates_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save templates: {e}")
    
    def get_all_templates(self) -> List[BankTemplate]:
        """Get all templates."""
        template_dicts = self._load_templates()
        return [BankTemplate(**t) for t in template_dicts]
    
    def get_template_by_type(self, bank_type: str) -> Optional[BankTemplate]:
        """Get template by bank type."""
        templates = self.get_all_templates()
        for template in templates:
            if template.bank_type == bank_type:
                return template
        return None
    
    def save_template(self, template: BankTemplate) -> bool:
        """Save or update a template."""
        try:
            templates = self._load_templates()
            
            # Find existing template or add new one
            updated = False
            for i, t in enumerate(templates):
                if t['bank_type'] == template.bank_type:
                    templates[i] = asdict(template)
                    updated = True
                    break
            
            if not updated:
                templates.append(asdict(template))
            
            self._save_templates(templates)
            return True
        except Exception as e:
            logger.error(f"Failed to save template: {e}")
            return False
    
    def delete_template(self, bank_type: str) -> bool:
        """Delete a template."""
        try:
            templates = self._load_templates()
            templates = [t for t in templates if t['bank_type'] != bank_type]
            self._save_templates(templates)
            return True
        except Exception as e:
            logger.error(f"Failed to delete template: {e}")
            return False

class AuditRepository:
    """Repository for audit trail and reconciliation history."""
    
    def __init__(self, db_file: str = "data/audit.db"):
        self.db_file = Path(db_file)
        self.db_file.parent.mkdir(exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database."""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reconciliation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    bank_name TEXT,
                    total_transactions INTEGER,
                    matched_transactions INTEGER,
                    match_rate REAL,
                    report_data TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    details TEXT,
                    user_id TEXT
                )
            """)
    
    def save_reconciliation(self, report: ReconciliationReport) -> bool:
        """Save reconciliation report."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.execute("""
                    INSERT INTO reconciliation_history 
                    (timestamp, bank_name, total_transactions, matched_transactions, match_rate, report_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    report.generated_at,
                    report.bank_statement.bank_name,
                    len(report.bank_statement.transactions),
                    len(report.matches),
                    len(report.matches) / len(report.bank_statement.transactions) if report.bank_statement.transactions else 0,
                    json.dumps(asdict(report))
                ))
            return True
        except Exception as e:
            logger.error(f"Failed to save reconciliation: {e}")
            return False
    
    def log_user_action(self, action_type: str, details: str, user_id: str = "default") -> bool:
        """Log user action for audit trail."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.execute("""
                    INSERT INTO user_actions (timestamp, action_type, details, user_id)
                    VALUES (?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    action_type,
                    details,
                    user_id
                ))
            return True
        except Exception as e:
            logger.error(f"Failed to log user action: {e}")
            return False

