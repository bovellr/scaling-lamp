# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.       

# ============================================================================
# APP CONTAINER
# ============================================================================

# services/app_container.py
"""
Dependency injection container to manage service lifecycles
and eliminate circular dependencies.
"""

from typing import Optional, Dict, Any
from .config_service import ConfigurationService, FileBasedConfigurationService, InMemoryConfigurationService, DatabaseConfigurationService
from .account_service import AccountService
from .data_transformation_service import DataTransformationService
from .optimized_reconciliation_service import OptimizedReconciliationService
from .performance_monitor import PerformanceMonitor
from viewmodels.upload_viewmodel import UploadViewModel
from models.bank_file_processor import BankFileProcessor

class ApplicationContainer:
    """Simple dependency injection container"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register_singleton(self, service_name: str, factory_func):
        """Register a singleton service"""
        self._services[service_name] = factory_func
    
    def get_service(self, service_name: str):
        """Get service instance (creates if singleton doesn't exist)"""
        if service_name in self._singletons:
            return self._singletons[service_name]
        
        if service_name in self._services:
            instance = self._services[service_name]()
            self._singletons[service_name] = instance
            return instance
        
        raise ValueError(f"Service {service_name} not registered")

# Global container instance
app_container = ApplicationContainer()


def setup_application_container(config_type: str = "file"):
    """Setup all service dependencies with configurable backend"""
    
    if config_type == "file":
        app_container.register_singleton(
            'config_service',
            lambda: FileBasedConfigurationService(
                accounts_file="config/bank_accounts.json",
                templates_file="config/bank_templates.json"
            )
        )
    elif config_type == "memory":
        app_container.register_singleton(
            'config_service',
            lambda: InMemoryConfigurationService()
        )
    elif config_type == "database":
        app_container.register_singleton(
            'config_service', 
            lambda: DatabaseConfigurationService("sqlite:///config.db")
        )
    else:
        raise ValueError(f"Unknown config type: {config_type}")
    
    # Rest of the container setup remains the same
    app_container.register_singleton(
        'account_service',
        lambda: AccountService(app_container.get_service('config_service'))
    )
    
    app_container.register_singleton(
        'upload_viewmodel', 
        lambda: UploadViewModel(app_container.get_service('config_service'))
    )
    
    # Register new optimized services
    app_container.register_singleton(
        'data_transformation_service',
        lambda: DataTransformationService()
    )
    
    app_container.register_singleton(
        'optimized_reconciliation_service',
        lambda: OptimizedReconciliationService()
    )
    
    app_container.register_singleton(
        'performance_monitor',
        lambda: PerformanceMonitor()
    )

def get_config_service() -> ConfigurationService:
    """Helper to get configuration service"""
    return app_container.get_service('config_service')

def get_account_service() -> AccountService:
    """Helper to get account service"""
    return app_container.get_service('account_service')

def get_upload_viewmodel() -> UploadViewModel:
    """Helper to get upload viewmodel"""
    return app_container.get_service('upload_viewmodel')

def get_data_transformation_service() -> DataTransformationService:
    """Helper to get data transformation service"""
    return app_container.get_service('data_transformation_service')

def get_optimized_reconciliation_service() -> OptimizedReconciliationService:
    """Helper to get optimized reconciliation service"""
    return app_container.get_service('optimized_reconciliation_service')

def get_performance_monitor() -> PerformanceMonitor:
    """Helper to get performance monitor"""
    return app_container.get_service('performance_monitor')