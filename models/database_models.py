# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.
# ================================
# MODELS - ERP Database Integration
# ================================

# models/database_models.py
"""
ERP database connection and query models.
Extends the existing data models with database connectivity.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConnection:
    """ERP database connection configuration."""
    name: str
    connection_type: str  # 'oracle', 'sqlserver', 'mysql', 'postgresql'
    host: str
    port: int
    database: str
    username: str
    password: str = ""  # Will be encrypted in storage
    service_name: Optional[str] = None  # For Oracle
    schema: Optional[str] = None
    connection_string: Optional[str] = None  # Custom connection string
    is_active: bool = True
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    last_tested: Optional[str] = None
    test_result: Optional[str] = None
    
    def get_connection_string(self) -> str:
        """Generate connection string based on database type."""
        if self.connection_string:
            return self.connection_string
        
        if self.connection_type == 'oracle':
            if self.service_name:
                return f"oracle+cx_oracle://{self.username}:{self.password}@{self.host}:{self.port}/?service_name={self.service_name}"
            else:
                return f"oracle+cx_oracle://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        
        elif self.connection_type == 'sqlserver':
            return f"mssql+pyodbc://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?driver=ODBC+Driver+17+for+SQL+Server"
        
        elif self.connection_type == 'postgresql':
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        
        elif self.connection_type == 'mysql':
            return f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        
        else:
            raise ValueError(f"Unsupported database type: {self.connection_type}")

@dataclass
class QueryParameter:
    """SQL query parameter definition."""
    name: str
    data_type: str  # 'string', 'integer', 'decimal', 'date', 'datetime'
    description: str
    default_value: Optional[str] = None
    is_required: bool = True
    validation_rule: Optional[str] = None  # Regex or custom validation
    
    def validate_value(self, value: Any) -> Tuple[bool, str]:
        """Validate parameter value."""
        if self.is_required and (value is None or value == ""):
            return False, f"Parameter '{self.name}' is required"
        
        if value is None or value == "":
            return True, ""
        
        try:
            if self.data_type == 'integer':
                int(value)
            elif self.data_type == 'decimal':
                float(value)
            elif self.data_type == 'date':
                if isinstance(value, str):
                    datetime.strptime(value, '%Y-%m-%d')
            elif self.data_type == 'datetime':
                if isinstance(value, str):
                    datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            
            return True, ""
        except (ValueError, TypeError) as e:
            return False, f"Invalid {self.data_type} value for '{self.name}': {str(e)}"

@dataclass
class ERPQueryTemplate:
    """ERP database query template with parameters."""
    name: str
    description: str
    sql_query: str
    parameters: List[QueryParameter] = field(default_factory=list)
    connection_name: str = ""
    expected_columns: List[str] = field(default_factory=list)  # Expected result columns
    created_by: str = "user"
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    last_modified: str = field(default_factory=lambda: datetime.now().isoformat())
    is_active: bool = True
    category: str = "transactions"  # 'transactions', 'accounts', 'vendors', etc.
    
    def validate_query(self) -> Tuple[bool, List[str]]:
        """Validate SQL query syntax and parameters."""
        errors = []
        
        # Basic SQL validation
        query_lower = self.sql_query.lower().strip()
        if not query_lower.startswith('select'):
            errors.append("Query must be a SELECT statement")
        
        if 'delete' in query_lower or 'drop' in query_lower or 'truncate' in query_lower:
            errors.append("Destructive SQL operations are not allowed")
        
        # Parameter validation
        import re
        param_pattern = r':(\w+)'
        query_params = set(re.findall(param_pattern, self.sql_query))
        defined_params = set(p.name for p in self.parameters)
        
        missing_params = query_params - defined_params
        if missing_params:
            errors.append(f"Missing parameter definitions: {', '.join(missing_params)}")
        
        unused_params = defined_params - query_params
        if unused_params:
            errors.append(f"Unused parameters defined: {', '.join(unused_params)}")
        
        return len(errors) == 0, errors

@dataclass
class ERPQueryExecution:
    """Record of ERP query execution."""
    query_name: str
    connection_name: str
    parameters: Dict[str, Any]
    execution_time: str = field(default_factory=lambda: datetime.now().isoformat())
    rows_returned: int = 0
    execution_duration: float = 0.0
    success: bool = False
    error_message: str = ""
    result_hash: Optional[str] = None  # For caching purposes