# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ================================
# VIEWMODELS - ERP Database Integration
# ================================

# viewmodels/erp_database_viewmodel.py
"""
ViewModel for ERP database operations.
"""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import pandas as pd
import logging

from .base_viewmodel import BaseViewModel
from models.erp_database_service import ERPDatabaseService
from models.erp_repository import ERPConfigurationRepository
from models.database_models import DatabaseConnection, ERPQueryTemplate, QueryParameter
from models.data_models import TransactionData
from config.settings import AppSettings

logger = logging.getLogger(__name__)

class ERPDatabaseViewModel(BaseViewModel):
    """ViewModel for ERP database operations."""
    
    def __init__(self):
        super().__init__()
        self.database_service = ERPDatabaseService()
        self.erp_service = ERPDatabaseService()
        self.config_repository = ERPConfigurationRepository()
        
        # State properties
        self._available_connections: List[DatabaseConnection] = []
        self._available_queries: List[ERPQueryTemplate] = []
        self._selected_connection: Optional[DatabaseConnection] = None
        self._selected_query: Optional[ERPQueryTemplate] = None
        self._query_parameters: Dict[str, Any] = {}
        self._query_results: pd.DataFrame = pd.DataFrame()
        self._erp_transactions: List[TransactionData] = []
        self._is_executing_query = False
        self._connection_test_result = "No connection selected"
        
        # Load existing configurations
        # Load existing configurations only if services initialized successfully
        if self.database_service is not None and self.config_repository is not None:
            self._load_configurations()
            #self._load_connections_and_queries()
        else:
            logger.error("Skipping configuration loading due to service initialization failure")
            
    
    def _load_connections_and_queries(self):
        """Load available connections and queries."""
        try:
            # Load existing connections
            existing_connections = self.database_service.get_available_connections()

            oracle_connection = self._create_oracle_connection_from_settings()
            if oracle_connection:
                # Add to ERP service if not already in existing connections
                self.database_service.add_connection(oracle_connection)
                existing_connections.append(oracle_connection)

            self._available_connections = existing_connections
            self.notify_property_changed('available_connections', self._available_connections)

            # Load existing queries
            existing_queries = self.database_service.get_available_queries()

            # Add default efin lloyds gl transaction queries if not present
            if not any(q.name == 'efin_lloyds_gl_transactions' for q in existing_queries):
                default_query = self._create_default_efin_query()
                if default_query:
                    self.database_service.add_query_template(default_query)
                    existing_queries.append(default_query)

            self._available_queries = self.database_service.get_available_queries('transactions')
            self.notify_property_changed('available_queries', self._available_queries)

            logger.info(f"Loaded {len(existing_connections)} connections and {len(existing_queries)} queries")

        except Exception as e:
            logger.error(f"Error loading connections and queries: {e}")
            self.error_message = f"Failed to load connections and queries: {str(e)}"
    
        self.notify_property_changed('available_queries', self._available_queries)
    
    def create_oracle_connection_from_settings(self):
        """Create Oracle connection from settings."""
        try:
            settings = AppSettings()

            if not settings.oracle_host or not settings.oracle_username:
                return None

            connection = DatabaseConnection(
                name="oracle_efin_live",
                connection_type="oracle",
                host=settings.oracle_host,
                port=settings.oracle_port,
                database=settings.oracle_service,
                username=settings.oracle_username,
                password=settings._get_oracle_password(),
                is_active=True,
                description="Oracle EFinancials Live",
                created_at=datetime.now().isoformat()
            )

            logger.info(f"Created Oracle connection from settings: {connection}")
            return connection

        except Exception as e:
            logger.error(f"Error creating Oracle connection from settings: {e}")
            return None
        
    
    def _load_configurations(self):
        """Load existing database configurations."""
        try:
            # Load connections
            connections_dict = self.config_repository.load_connections()
            for connection in connections_dict.values():
                self.database_service.add_connection(connection)
            
            # Load query templates
            templates_dict = self.config_repository.load_query_templates()
            for template in templates_dict.values():
                self.database_service.add_query_template(template)
            
            self._refresh_available_items()
            
        except Exception as e:
            logger.error(f"Error loading connections and queries: {e}")
            self.error_message = f"Failed to load configurations: {str(e)}"
    
    def _refresh_available_items(self):
        """Refresh available connections and queries."""
        self._available_connections = self.database_service.get_available_connections()
        self._available_queries = self.database_service.get_available_queries('transactions')
        
        self.notify_property_changed('available_connections', self._available_connections)
        self.notify_property_changed('available_queries', self._available_queries)
    

    def _create_default_oracle_query(self):
        """Create default EFIN Lloyds GL Transactions query."""
        try:
            from models.database_models import QueryParameter
            parameters = [ 
                QueryParameter(
                    name="start_date", 
                    data_type="date", 
                    description="Start Date", 
                    default_value=datetime.now().replace(day=1).strftime('%Y-%m-%d').isoformat(), 
                    is_required=True),
                QueryParameter(
                    name="end_date", 
                    data_type="date", 
                    description="End Date", 
                    default_value=datetime.now().strftime('%Y-%m-%d').isoformat(), 
                    is_required=True),
                QueryParameter(
                    name="account_code", 
                    data_type="string", 
                    description="Account Code", 
                    default_value= "152000", 
                    is_required=True)
            ]

            sql_query = self.config_repository.get_query_template("transactions", "get_lloyds_main_transactions").query
            if not sql_query:
                return None

            template = ERPQueryTemplate(
                name="lloyds_main_transactions",
                description="Lloyds main transactions",
                sql_query=sql_query,
                parameters=parameters
            )
            return template

        except Exception as e:
            logger.error(f"Error creating default Oracle query: {e}")
            return None

    def _load_queries_for_connection(self):
        """Load queries available for the selected connection."""

        if not self._selected_connection:
            return

        try:
            connection_queries = [
                q for q in self._available_queries 
                if q.connection_name == self._selected_connection.name
            ]
            self.notify_property_changed('available_queries', connection_queries)
        
        except Exception as e:
            logger.error(f"Error loading queries for connection: {e}")
            
            

    def _create_default_query(self):
        """Create default query for the selected connection."""
        if self._selected_connection.connection_type == "oracle":
            return self._create_default_oracle_query()
        return None
    
    
    
    # Properties
    @property
    def available_connections(self) -> List[DatabaseConnection]:
        return self._available_connections
    
    @property
    def available_queries(self) -> List[ERPQueryTemplate]:
        return self._available_queries
    
    @property
    def selected_connection(self) -> Optional[DatabaseConnection]:
        return self._selected_connection
    
    @selected_connection.setter
    def selected_connection(self, connection: Optional[DatabaseConnection]):
        if self._selected_connection != connection:
            self._selected_connection = connection
            self.notify_property_changed('selected_connection', connection)
            self._load_queries_for_connection()
    
    @property
    def selected_query(self) -> Optional[ERPQueryTemplate]:
        return self._selected_query
    
    @selected_query.setter  
    def selected_query(self, query: Optional[ERPQueryTemplate]):
        if self._selected_query != query:
            self._selected_query = query
            self._query_parameters = {}  # Reset parameters
                        
            # Initialize default parameter values
            if query:
                for param in query.parameters:
                    if param.default_value:
                        self._query_parameters[param.name] = param.default_value
            
            self.notify_property_changed('selected_query', query)
            self.notify_property_changed('query_parameters', self._query_parameters)
    
    @property
    def query_parameters(self) -> Dict[str, Any]:
        return self._query_parameters
    
    @property
    def query_results(self) -> pd.DataFrame:
        return self._query_results
    
    @property
    def erp_transactions(self) -> List[TransactionData]:
        return self._erp_transactions
    
    @property
    def is_executing_query(self) -> bool:
        return self._is_executing_query
    
    @property
    def connection_test_result(self) -> str:
        return self._connection_test_result
    
    @property
    def can_execute_query(self) -> bool:
        """Check if query can be executed."""
        return (self._selected_connection is not None and
                self._selected_query is not None and
                not self._is_executing_query)
    
    # Commands
    def test_connection_command(self, connection: DatabaseConnection) -> bool:
        """Test database connection."""
        try:
            success, message = self._erp_service.test_connection(connection.name)
            
            if success:
                self._connection_test_result = f"Connection test successful: {message}"
            else:
                self._connection_test_result = f"Connection test failed: {message}"
            
            self.notify_property_changed('connection_test_result', self._connection_test_result)
            logger.info(f"Connection test for '{connection.name}': {success} - {message}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error testing connection: {e}")
            self._connection_test_result = f"Connection test error: {str(e)}"
            self.notify_property_changed('connection_test_result', self._connection_test_result)
            return False
    
    def update_parameter_command(self, parameter_name: str, value: Any):
        """Update query parameter value."""
        self._query_parameters[parameter_name] = value
        self.notify_property_changed('query_parameters', self._query_parameters)
    
    def execute_query_command(self) -> bool:
        """Execute selected query with parameters."""
        if not self.can_execute_query:
            self.error_message = "Cannot execute query: missing connection or query selection"
            return False
        
        try:
            self._is_executing_query = True
            self.clear_error()
            self.notify_property_changed('is_executing_query', True)
            
            # Execute query
            success, df, message = self.database_service.execute_query(
                self._selected_query.name,
                self._query_parameters
            )
            
            if success:
                self._query_results = df
                
                # Convert to transactions if possible
                if not df.empty:
                    # Use expected columns from query template for mapping
                    column_mapping = self._create_column_mapping(df.columns.tolist())

                    transactions = self.database_service.convert_to_transactions(df, column_mapping)
                    self._erp_transactions = transactions
                else:
                    self._erp_transactions = []
                
                self.notify_property_changed('query_results', df)
                self.notify_property_changed('erp_transactions', self._erp_transactions)
                
                logger.info(f"Query execution successful: {len(transactions)} transactions")
                # Update status
                self._connection_test_result = {message}
                self.notify_property_changed('connection_test_result', self._connection_test_result)
            else:
                self.error_message = f"Query execution failed: {message}"
                logger.error(f"Query execution failed: {message}")
                self._connection_test_result = {message}
                self.notify_property_changed('connection_test_result', self._connection_test_result)
                
            
            return success
            
        except Exception as e:
            error_msg = f"Query execution failed: {str(e)}"
            self.error_message = error_msg
            self._connection_test_result = {error_msg}
            self.notify_property_changed('connection_test_result', self._connection_test_result)
            return False
        finally:
            self._is_executing_query = False
            self.notify_property_changed('is_executing_query', False)
    
    def _create_column_mapping(self, available_columns: List[str]) -> Dict[str, str]:
        """Create column mapping based on available columns."""
        mapping = {}
        available_lower = [col.lower() for col in available_columns]
        
        # Common column name patterns
        patterns = {
            'date': ['date', 'transaction_date', 'posting_date', 'value_date', 'trans_date'],
            'description': ['description', 'narrative', 'details', 'memo'],
            'amount': ['amount', 'value', 'transaction_amount', 'debit_amount', 'credit_amount'],
            'reference': ['reference', 'ref', 'transaction_ref', 'doc_number', 'cheque_ref']
        }
        
        for logical_name, possible_names in patterns.items():
            for pattern in possible_names:
                for i, col in enumerate(available_lower):
                    if pattern in col:
                        mapping[logical_name] = available_columns[i]
                        break
                if logical_name in mapping:
                    break
        
        return mapping
    
    def save_connection_command(self, connection: DatabaseConnection) -> bool:
        """Save database connection."""
        try:
            success = self._erp_service.add_connection(connection)

            if success:
                # Refresh connections list
                self._available_connections = self._erp_service.get_available_connections()
                self.notify_property_changed('available_connections', self._available_connections)
                logger.info(f"Connection '{connection.name}' saved successfully")

            return success
      
        except Exception as e:
            logger.error(f"Error saving connection: {str(e)}")
            self.error_message = f"Error saving connection: {str(e)}"
            return False
    
    def save_query_template_command(self, template: ERPQueryTemplate) -> bool:
        """Save query template."""
        try:
            success = self._erp_service.add_query_template(template)
            
            if success:
                # Refresh queries list
                self._available_queries = self._erp_service.get_available_queries()
                self.notify_property_changed('available_queries', self._available_queries)
                logger.info(f"Query template '{template.name}' saved successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving query template: {e}")
            self.error_message = f"Failed to save query template: {str(e)}"
            return False
    
    def delete_connection_command(self, connection_name: str) -> bool:
        """Delete database connection."""
        try:
            if self.config_repository.delete_connection(connection_name):
                self._refresh_available_items()
                return True
            return False
        except Exception as e:
            self.error_message = f"Error deleting connection: {str(e)}"
            return False
    
    def clear_cache_command(self):
        """Clear query result cache."""
        self.database_service.clear_cache()
        self._connection_test_result = "Cache cleared"
        self.notify_property_changed('connection_test_result', self._connection_test_result)

    