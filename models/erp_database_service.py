# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.
# ================================
# models/erp_database_service.py
# ================================
"""
ERP database service for executing queries and managing connections.
"""

import pandas as pd
import sqlalchemy as sa
from sqlalchemy import create_engine, text
from typing import Dict, List, Optional, Tuple, Any
import hashlib
import time
import logging
import json
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

from .database_models import DatabaseConnection, ERPQueryTemplate, ERPQueryExecution, QueryParameter
from .data_models import TransactionData
from .text_utils import normalize_description

class ERPDatabaseService:
    """Service for ERP database operations."""
    
    def __init__(self):
        self.connections: Dict[str, DatabaseConnection] = {}
        self.query_templates: Dict[str, ERPQueryTemplate] = {}
        self.execution_cache: Dict[str, pd.DataFrame] = {}  # Simple caching
        self._engines: Dict[str, sa.Engine] = {}
    
    def add_connection(self, connection: DatabaseConnection) -> bool:
        """Add or update database connection."""
        try:
            self.connections[connection.name] = connection
            # Clear cached engine if it exists
            if connection.name in self._engines:
                self._engines[connection.name].dispose()
                del self._engines[connection.name]
            return True
        except Exception as e:
            logger.error(f"Failed to add connection {connection.name}: {e}")
            return False
    
    def test_connection(self, connection_name: str) -> Tuple[bool, str]:
        """Test database connection."""
        try:
            connection = self.connections.get(connection_name)
            if not connection:
                return False, f"Connection '{connection_name}' not found"
            
            engine = self._get_engine(connection)
            
            # Test with simple query
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 FROM DUAL"))  # Oracle syntax
                result.fetchone()
            
            # Update connection test result
            connection.last_tested = datetime.now().isoformat()
            connection.test_result = "Success"
            
            return True, "Connection successful"
            
        except Exception as e:
            error_msg = str(e)
            if connection:
                connection.last_tested = datetime.now().isoformat()
                connection.test_result = f"Failed: {error_msg}"
            
            logger.error(f"Connection test failed for {connection_name}: {e}")
            return False, error_msg
    
    def _get_engine(self, connection: DatabaseConnection) -> sa.Engine:
        """Get or create database engine."""
        if connection.name not in self._engines:
            connection_string = connection.get_connection_string()
            
            # Configure engine based on database type
            engine_kwargs = {
                'echo': False,  # Set to True for SQL debugging
                'pool_pre_ping': True,  # Verify connections before use
                'pool_recycle': 3600,   # Recycle connections every hour
            }
            
            if connection.connection_type == 'oracle':
                engine_kwargs.update({
                    'max_identifier_length': 30,  # Oracle limitation
                })
            
            self._engines[connection.name] = create_engine(connection_string, **engine_kwargs)
        
        return self._engines[connection.name]
    
    @contextmanager
    def get_connection(self, connection_name: str):
        """Context manager for database connections."""
        connection = self.connections.get(connection_name)
        if not connection:
            raise ValueError(f"Connection '{connection_name}' not found")
        
        engine = self._get_engine(connection)
        conn = engine.connect()
        
        try:
            yield conn
        finally:
            conn.close()
    
    def add_query_template(self, template: ERPQueryTemplate) -> bool:
        """Add or update query template."""
        try:
            # Validate query
            is_valid, errors = template.validate_query()
            if not is_valid:
                logger.error(f"Invalid query template {template.name}: {errors}")
                return False
            
            template.last_modified = datetime.now().isoformat()
            self.query_templates[template.name] = template
            return True
            
        except Exception as e:
            logger.error(f"Failed to add query template {template.name}: {e}")
            return False
    
    def execute_query(self, template_name: str, parameters: Dict[str, Any]) -> Tuple[bool, pd.DataFrame, str]:
        """Execute ERP query with parameters."""
        start_time = time.time()
        
        try:
            # Get template
            template = self.query_templates.get(template_name)
            if not template:
                return False, pd.DataFrame(), f"Query template '{template_name}' not found"
            
            # Validate parameters
            validation_error = self._validate_parameters(template, parameters)
            if validation_error:
                return False, pd.DataFrame(), validation_error
            
            # Check cache
            cache_key = self._generate_cache_key(template_name, parameters)
            if cache_key in self.execution_cache:
                logger.info(f"Returning cached result for {template_name}")
                return True, self.execution_cache[cache_key], "Cached result"
            
            # Execute query
            with self.get_connection(template.connection_name) as conn:
                # Replace parameters in query
                query = text(template.sql_query)
                result = conn.execute(query, parameters)
                
                # Convert to DataFrame
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
                
                # Cache result
                self.execution_cache[cache_key] = df
                
                # Log execution
                execution_time = time.time() - start_time
                execution = ERPQueryExecution(
                    query_name=template_name,
                    connection_name=template.connection_name,
                    parameters=parameters,
                    rows_returned=len(df),
                    execution_duration=execution_time,
                    success=True,
                    result_hash=cache_key
                )
                
                logger.info(f"Query {template_name} executed successfully: {len(df)} rows in {execution_time:.2f}s")
                return True, df, f"Retrieved {len(df)} records"
        
        except Exception as e:
            error_msg = f"Query execution failed: {str(e)}"
            logger.error(f"Query {template_name} failed: {e}")
            
            # Log failed execution
            execution = ERPQueryExecution(
                query_name=template_name,
                connection_name=template.connection_name if template else "",
                parameters=parameters,
                execution_duration=time.time() - start_time,
                success=False,
                error_message=error_msg
            )
            
            return False, pd.DataFrame(), error_msg
    
    def _validate_parameters(self, template: ERPQueryTemplate, parameters: Dict[str, Any]) -> Optional[str]:
        """Validate query parameters."""
        for param in template.parameters:
            value = parameters.get(param.name)
            is_valid, error_msg = param.validate_value(value)
            if not is_valid:
                return error_msg
        return None
    
    def _generate_cache_key(self, template_name: str, parameters: Dict[str, Any]) -> str:
        """Generate cache key for query results."""
        param_str = json.dumps(parameters, sort_keys=True, default=str)
        key_data = f"{template_name}:{param_str}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def convert_to_transactions(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> List[TransactionData]:
        """Convert ERP query results to TransactionData objects."""
        transactions = []
        
        # Default column mapping
        default_mapping = {
            'date': 'date',
            'description': 'description', 
            'amount': 'amount',
            'reference': 'reference'
        }
        
        # Use provided mapping or defaults
        mapping = {**default_mapping, **column_mapping}
        
        for _, row in df.iterrows():
            try:
                date_str = str(row[mapping['date']]) if mapping['date'] in row else ""
                description = str(row[mapping['description']]) if mapping['description'] in row else ""
                amount = float(row[mapping['amount']]) if mapping['amount'] in row else 0.0
                reference = (
                    str(row[mapping['reference']])
                    if mapping['reference'] in row and pd.notna(row[mapping['reference']])
                    else None
                )

                normalized_description = normalize_description(description, date_str)
                transaction = TransactionData(
                    date=date_str,
                    description=description,
                    amount=amount,
                    reference=reference,
                    normalized_description=normalized_description,
                )
                transactions.append(transaction)
            except Exception as e:
                logger.warning(f"Failed to convert row to transaction: {e}")
                continue
        
        return transactions
    
    def get_available_connections(self) -> List[DatabaseConnection]:
        """Get list of available database connections."""
        return [conn for conn in self.connections.values() if conn.is_active]
    
    def get_available_queries(self, category: Optional[str] = None) -> List[ERPQueryTemplate]:
        """Get list of available query templates."""
        queries = [q for q in self.query_templates.values() if q.is_active]
        
        if category:
            queries = [q for q in queries if q.category == category]
        
        return queries
    
    def clear_cache(self):
        """Clear query result cache."""
        self.execution_cache.clear()
        logger.info("Query cache cleared")