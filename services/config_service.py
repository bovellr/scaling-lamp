# services/config_service.py (CORRECTED - Complete Implementation)
"""
Complete implementation of ConfigurationService with all abstract methods implemented.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import logging
from threading import RLock
from datetime import datetime

from models.data_models import BankTemplate, BankStatement
from config.defaults import (
    DEFAULT_BANK_ACCOUNTS, DEFAULT_BANK_TEMPLATES, 
    LEGACY_TRANSFORMER_MAPPINGS, DefaultBankAccount, DefaultBankTemplate
)

logger = logging.getLogger(__name__)

class ConfigurationService(ABC):
    """Abstract base for configuration management"""
    
    @abstractmethod
    def get_bank_accounts(self) -> Dict[str, Dict[str, Any]]:
        """Get all bank account configurations"""
        pass
    
    @abstractmethod
    def get_bank_templates(self) -> List[BankTemplate]:
        """Get all bank template configurations"""  
        pass
    
    @abstractmethod
    def get_template_by_type(self, bank_type: str) -> Optional[BankTemplate]:
        """Get template by bank type with legacy mapping support"""
        pass
    
    @abstractmethod
    def save_bank_accounts(self, accounts: Dict[str, Dict[str, Any]]) -> bool:
        """Save bank account configurations"""
        pass
    
    @abstractmethod
    def save_bank_templates(self, templates: List[BankTemplate]) -> bool:
        """Save bank template configurations"""
        pass
    
    @abstractmethod
    def add_bank_account(self, name: str, config: Dict[str, Any]) -> bool:
        """Add a new bank account"""
        pass
    
    @abstractmethod
    def update_bank_account(self, name: str, config: Dict[str, Any]) -> bool:
        """Update existing bank account"""
        pass
    
    @abstractmethod
    def delete_bank_account(self, name: str) -> bool:
        """Delete bank account"""
        pass
    
    @abstractmethod
    def add_bank_template(self, template: BankTemplate) -> bool:
        """Add a new bank template"""
        pass
    
    @abstractmethod
    def update_bank_template(self, template: BankTemplate) -> bool:
        """Update existing bank template"""
        pass
    
    @abstractmethod
    def delete_bank_template(self, bank_type: str) -> bool:
        """Delete bank template by type"""
        pass
    
    @abstractmethod
    def reload_configurations(self) -> bool:
        """Reload all configurations from storage"""
        pass
    
    @abstractmethod
    def validate_account_config(self, config: Dict[str, Any]) -> bool:
        """Validate account configuration"""
        pass
    
    @abstractmethod
    def validate_template_config(self, template: BankTemplate) -> bool:
        """Validate template configuration"""
        pass


class FileBasedConfigurationService(ConfigurationService):
    """COMPLETE file-based implementation of configuration service"""
    
    def __init__(
        self,
        accounts_file: str = "config/bank_accounts.json",
        templates_file: str = "config/bank_templates.json",
        event_bus: Optional[object] = None
    ):
        self.accounts_file = Path(accounts_file)
        self.templates_file = Path(templates_file)
        self.event_bus = event_bus
        self._lock = RLock()
        
        # Ensure directories exist
        self.accounts_file.parent.mkdir(parents=True, exist_ok=True)
        self.templates_file.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory caches
        self._accounts_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._templates_cache: Optional[List[BankTemplate]] = None
        
        # Initialize caches
        self._load_all_configurations()
    
    def _load_all_configurations(self):
        """Load all configurations into memory"""
        self._load_accounts_cache()
        self._load_templates_cache()
    
    def _load_accounts_cache(self):
        """Load account configurations from file or create defaults"""
        with self._lock:
            if self.accounts_file.exists():
                try:
                    with open(self.accounts_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, dict) and data:
                        self._accounts_cache = data
                        logger.info(f"Loaded {len(data)} bank accounts from file")
                        return
                    else:
                        raise ValueError("Invalid accounts file structure")
                        
                except Exception as e:
                    logger.error(f"Failed to load accounts file: {e}")
            
            # Create defaults
            logger.info("Creating default bank accounts configuration")
            self._accounts_cache = self._convert_default_accounts_to_dict()
            self._save_accounts_to_file()
    
    def _load_templates_cache(self):
        """Load template configurations from file or create defaults"""
        with self._lock:
            if self.templates_file.exists():
                try:
                    with open(self.templates_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    templates = []
                    template_list = data.get('templates', []) if isinstance(data, dict) else data
                    
                    for template_dict in template_list:
                        # Ensure required fields exist
                        template_dict.setdefault('created_by', 'system')
                        template_dict.setdefault('created_date', datetime.now().isoformat())
                        template_dict.setdefault('is_active', True)
                        templates.append(BankTemplate(**template_dict))
                    
                    if templates:
                        self._templates_cache = templates
                        logger.info(f"Loaded {len(templates)} bank templates from file")
                        return
                    else:
                        raise ValueError("No valid templates found in file")
                        
                except Exception as e:
                    logger.error(f"Failed to load templates file: {e}")
            
            # Create defaults
            logger.info("Creating default bank templates configuration")
            self._templates_cache = self._convert_default_templates_to_objects()
            self._save_templates_to_file()
    
    def _convert_default_accounts_to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Convert default account dataclasses to dict format"""
        result = {}
        for name, account in DEFAULT_BANK_ACCOUNTS.items():
            result[name] = {
                "account_number": account.account_number,
                "sort_code": account.sort_code,
                "transformer": account.transformer,
                "erp_account_code": account.erp_account_code,
                "erp_account_name": account.erp_account_name,
                "statement_format": account.statement_format,
                "currency": account.currency
            }
        return result
    
    def _convert_default_templates_to_objects(self) -> List[BankTemplate]:
        """Convert default template dataclasses to BankTemplate objects"""
        templates = []
        for template_def in DEFAULT_BANK_TEMPLATES.values():
            templates.append(BankTemplate(
                name=template_def.name,
                bank_type=template_def.bank_type,
                header_keywords=template_def.header_keywords,
                date_patterns=template_def.date_patterns,
                skip_keywords=template_def.skip_keywords,
                column_mapping=template_def.column_mapping,
                description=template_def.description,
                created_by='system',
                created_date=datetime.now().isoformat(),
                is_active=True
            ))
        return templates
    
    # ========================================================================
    # ABSTRACT METHOD IMPLEMENTATIONS - ACCOUNT OPERATIONS
    # ========================================================================
    
    def get_bank_accounts(self) -> Dict[str, Dict[str, Any]]:
        """Get all bank account configurations"""
        with self._lock:
            if self._accounts_cache is None:
                self._load_accounts_cache()
            return json.loads(json.dumps(self._accounts_cache))  # Deep copy
    
    def save_bank_accounts(self, accounts: Dict[str, Dict[str, Any]]) -> bool:
        """Save bank account configurations"""
        with self._lock:
            try:
                # Validate all accounts before saving
                for name, config in accounts.items():
                    if not self.validate_account_config(config):
                        logger.error(f"Invalid account configuration for '{name}'")
                        return False
                
                self._accounts_cache = accounts.copy()
                return self._save_accounts_to_file()
            except Exception as e:
                logger.error(f"Failed to save bank accounts: {e}")
                return False
    
    def add_bank_account(self, name: str, config: Dict[str, Any]) -> bool:
        """Add a new bank account"""
        with self._lock:
            accounts = self.get_bank_accounts()
            
            if name in accounts:
                logger.warning(f"Account '{name}' already exists")
                return False
            
            if not self.validate_account_config(config):
                logger.error(f"Invalid configuration for account '{name}'")
                return False
            
            accounts[name] = config.copy()
            return self.save_bank_accounts(accounts)
    
    def update_bank_account(self, name: str, config: Dict[str, Any]) -> bool:
        """Update existing bank account"""
        with self._lock:
            accounts = self.get_bank_accounts()
            
            if name not in accounts:
                logger.warning(f"Account '{name}' does not exist")
                return False
            
            if not self.validate_account_config(config):
                logger.error(f"Invalid configuration for account '{name}'")
                return False
            
            accounts[name] = config.copy()
            return self.save_bank_accounts(accounts)
    
    def delete_bank_account(self, name: str) -> bool:
        """Delete bank account"""
        with self._lock:
            accounts = self.get_bank_accounts()
            
            if name not in accounts:
                logger.warning(f"Account '{name}' not found")
                return False
            
            del accounts[name]
            return self.save_bank_accounts(accounts)
    
    def validate_account_config(self, config: Dict[str, Any]) -> bool:
        """Validate account configuration"""
        required_fields = {
            "account_number",
            "transformer",
            "erp_account_code",
            "erp_account_name",
            "currency"
        }
        
        if not isinstance(config, dict):
            return False
        
        if not required_fields.issubset(config.keys()):
            missing = required_fields - config.keys()
            logger.error(f"Missing required fields: {missing}")
            return False
        
        # Additional validation
        if not config.get("account_number", "").strip():
            logger.error("Account number cannot be empty")
            return False
        
        if not config.get("transformer", "").strip():
            logger.error("Transformer cannot be empty")
            return False
        
        return True
    
    # ========================================================================
    # ABSTRACT METHOD IMPLEMENTATIONS - TEMPLATE OPERATIONS
    # ========================================================================
    
    def get_bank_templates(self) -> List[BankTemplate]:
        """Get all bank template configurations"""
        with self._lock:
            if self._templates_cache is None:
                self._load_templates_cache()
            return self._templates_cache.copy()  # Shallow copy is fine for immutable objects
    
    def get_template_by_type(self, bank_type: str) -> Optional[BankTemplate]:
        """Get template by bank type with legacy mapping support"""
        # Handle legacy transformer mappings
        actual_type = LEGACY_TRANSFORMER_MAPPINGS.get(bank_type, bank_type)
        
        templates = self.get_bank_templates()
        for template in templates:
            if template.bank_type == actual_type:
                return template
        
        logger.warning(f"No template found for bank type: {bank_type} (mapped to: {actual_type})")
        return None
    
    def save_bank_templates(self, templates: List[BankTemplate]) -> bool:
        """Save bank template configurations"""
        with self._lock:
            try:
                # Validate all templates before saving
                for template in templates:
                    if not self.validate_template_config(template):
                        logger.error(f"Invalid template configuration for '{template.name}'")
                        return False
                
                self._templates_cache = templates.copy()
                return self._save_templates_to_file()
            except Exception as e:
                logger.error(f"Failed to save bank templates: {e}")
                return False
    
    def add_bank_template(self, template: BankTemplate) -> bool:
        """Add a new bank template"""
        with self._lock:
            templates = self.get_bank_templates()
            
            # Check if template with same bank_type already exists
            for existing in templates:
                if existing.bank_type == template.bank_type:
                    logger.warning(f"Template for bank type '{template.bank_type}' already exists")
                    return False
            
            if not self.validate_template_config(template):
                logger.error(f"Invalid template configuration for '{template.name}'")
                return False
            
            templates.append(template)
            return self.save_bank_templates(templates)
    
    def update_bank_template(self, template: BankTemplate) -> bool:
        """Update existing bank template"""
        with self._lock:
            templates = self.get_bank_templates()
            
            # Find and update existing template
            updated = False
            for i, existing in enumerate(templates):
                if existing.bank_type == template.bank_type:
                    if not self.validate_template_config(template):
                        logger.error(f"Invalid template configuration for '{template.name}'")
                        return False
                    
                    templates[i] = template
                    updated = True
                    break
            
            if not updated:
                logger.warning(f"Template for bank type '{template.bank_type}' not found")
                return False
            
            return self.save_bank_templates(templates)
    
    def delete_bank_template(self, bank_type: str) -> bool:
        """Delete bank template by type"""
        with self._lock:
            templates = self.get_bank_templates()
            
            # Find and remove template
            original_count = len(templates)
            templates = [t for t in templates if t.bank_type != bank_type]
            
            if len(templates) == original_count:
                logger.warning(f"Template for bank type '{bank_type}' not found")
                return False
            
            return self.save_bank_templates(templates)
    
    def validate_template_config(self, template: BankTemplate) -> bool:
        """Validate template configuration"""
        if not isinstance(template, BankTemplate):
            logger.error("Template must be a BankTemplate instance")
            return False
        
        if not template.name or not template.name.strip():
            logger.error("Template name cannot be empty")
            return False
        
        if not template.bank_type or not template.bank_type.strip():
            logger.error("Template bank_type cannot be empty")
            return False
        
        if not template.header_keywords or not isinstance(template.header_keywords, list):
            logger.error("Template must have valid header_keywords list")
            return False
        
        if not template.date_patterns or not isinstance(template.date_patterns, list):
            logger.error("Template must have valid date_patterns list")
            return False
        
        if not template.column_mapping or not isinstance(template.column_mapping, dict):
            logger.error("Template must have valid column_mapping dict")
            return False
        
        # Validate regex patterns
        import re
        for pattern in template.date_patterns:
            try:
                re.compile(pattern)
            except re.error as e:
                logger.error(f"Invalid regex pattern '{pattern}': {e}")
                return False
        
        return True
    
    # ========================================================================
    # ABSTRACT METHOD IMPLEMENTATIONS - UTILITY OPERATIONS
    # ========================================================================
    
    def reload_configurations(self) -> bool:
        """Reload all configurations from storage"""
        with self._lock:
            try:
                self._accounts_cache = None
                self._templates_cache = None
                self._load_all_configurations()
                
                if self.event_bus:
                    self.event_bus.publish("config.reloaded", {
                        "accounts": self._accounts_cache,
                        "templates": self._templates_cache
                    })
                
                logger.info("Successfully reloaded all configurations")
                return True
                
            except Exception as e:
                logger.error(f"Failed to reload configurations: {e}")
                return False
    
    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================
    
    def _save_accounts_to_file(self) -> bool:
        """Save accounts cache to file atomically"""
        try:
            temp_file = self.accounts_file.with_suffix('.tmp')
            backup_file = self.accounts_file.with_suffix('.bak')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self._accounts_cache, f, indent=2, ensure_ascii=False)
            
            # Create backup if original exists
            if self.accounts_file.exists():
                self.accounts_file.replace(backup_file)
            
            # Atomic rename
            temp_file.replace(self.accounts_file)
            
            if self.event_bus:
                self.event_bus.publish("accounts.updated", self._accounts_cache)
            
            logger.info(f"Saved {len(self._accounts_cache)} bank accounts")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save accounts to file: {e}")
            if temp_file.exists():
                temp_file.unlink(missing_ok=True)
            return False
    
    def _save_templates_to_file(self) -> bool:
        """Save templates cache to file atomically"""
        try:
            temp_file = self.templates_file.with_suffix('.tmp')
            backup_file = self.templates_file.with_suffix('.bak')
            
            # Convert templates to dict format for JSON
            templates_dict = {
                "templates": [
                    {
                        "name": t.name,
                        "bank_type": t.bank_type,
                        "header_keywords": t.header_keywords,
                        "date_patterns": t.date_patterns,
                        "skip_keywords": t.skip_keywords,
                        "column_mapping": t.column_mapping,
                        "description": t.description,
                        "created_by": getattr(t, 'created_by', 'system'),
                        "created_date": getattr(t, 'created_date', datetime.now().isoformat()),
                        "is_active": getattr(t, 'is_active', True)
                    }
                    for t in self._templates_cache
                ]
            }
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(templates_dict, f, indent=2, ensure_ascii=False)
            
            # Create backup if original exists
            if self.templates_file.exists():
                self.templates_file.replace(backup_file)
            
            # Atomic rename
            temp_file.replace(self.templates_file)
            
            if self.event_bus:
                self.event_bus.publish("templates.updated", self._templates_cache)
                
            logger.info(f"Saved {len(self._templates_cache)} bank templates")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save templates to file: {e}")
            if temp_file.exists():
                temp_file.unlink(missing_ok=True)
            return False

# services/config_service.py (ADDITIONAL IMPLEMENTATIONS)

class InMemoryConfigurationService(ConfigurationService):
    """In-memory implementation for testing"""
    
    def __init__(self):
        self._accounts = self._get_default_accounts()
        self._templates = self._get_default_templates()
    
    def get_bank_accounts(self) -> Dict[str, Dict[str, Any]]:
        return json.loads(json.dumps(self._accounts))  # Deep copy
    
    def get_bank_templates(self) -> List[BankTemplate]:
        return self._templates.copy()
    
    def get_template_by_type(self, bank_type: str) -> Optional[BankTemplate]:
        actual_type = LEGACY_TRANSFORMER_MAPPINGS.get(bank_type, bank_type)
        for template in self._templates:
            if template.bank_type == actual_type:
                return template
        return None
    
    def save_bank_accounts(self, accounts: Dict[str, Dict[str, Any]]) -> bool:
        for name, config in accounts.items():
            if not self.validate_account_config(config):
                return False
        self._accounts = accounts.copy()
        return True
    
    def save_bank_templates(self, templates: List[BankTemplate]) -> bool:
        for template in templates:
            if not self.validate_template_config(template):
                return False
        self._templates = templates.copy()
        return True
    
    def add_bank_account(self, name: str, config: Dict[str, Any]) -> bool:
        if name in self._accounts:
            return False
        if not self.validate_account_config(config):
            return False
        self._accounts[name] = config.copy()
        return True
    
    def update_bank_account(self, name: str, config: Dict[str, Any]) -> bool:
        if name not in self._accounts:
            return False
        if not self.validate_account_config(config):
            return False
        self._accounts[name] = config.copy()
        return True
    
    def delete_bank_account(self, name: str) -> bool:
        if name not in self._accounts:
            return False
        del self._accounts[name]
        return True
    
    def add_bank_template(self, template: BankTemplate) -> bool:
        for existing in self._templates:
            if existing.bank_type == template.bank_type:
                return False
        if not self.validate_template_config(template):
            return False
        self._templates.append(template)
        return True
    
    def update_bank_template(self, template: BankTemplate) -> bool:
        for i, existing in enumerate(self._templates):
            if existing.bank_type == template.bank_type:
                if not self.validate_template_config(template):
                    return False
                self._templates[i] = template
                return True
        return False
    
    def delete_bank_template(self, bank_type: str) -> bool:
        original_count = len(self._templates)
        self._templates = [t for t in self._templates if t.bank_type != bank_type]
        return len(self._templates) < original_count
    
    def reload_configurations(self) -> bool:
        # In-memory implementation doesn't need reloading
        return True
    
    def validate_account_config(self, config: Dict[str, Any]) -> bool:
        required_fields = {"account_number", "transformer", "erp_account_code", "erp_account_name", "currency"}
        return isinstance(config, dict) and required_fields.issubset(config.keys())
    
    def validate_template_config(self, template: BankTemplate) -> bool:
        return (isinstance(template, BankTemplate) and 
                template.name and template.bank_type and 
                template.header_keywords and template.date_patterns and 
                template.column_mapping)
    
    def _get_default_accounts(self) -> Dict[str, Dict[str, Any]]:
        # Convert from defaults
        result = {}
        for name, account in DEFAULT_BANK_ACCOUNTS.items():
            result[name] = {
                "account_number": account.account_number,
                "sort_code": account.sort_code,
                "transformer": account.transformer,
                "erp_account_code": account.erp_account_code,
                "erp_account_name": account.erp_account_name,
                "statement_format": account.statement_format,
                "currency": account.currency
            }
        return result
    
    def _get_default_templates(self) -> List[BankTemplate]:
        templates = []
        for template_def in DEFAULT_BANK_TEMPLATES.values():
            templates.append(BankTemplate(
                name=template_def.name,
                bank_type=template_def.bank_type,
                header_keywords=template_def.header_keywords,
                date_patterns=template_def.date_patterns,
                skip_keywords=template_def.skip_keywords,
                column_mapping=template_def.column_mapping,
                description=template_def.description,
                created_by='system',
                created_date=datetime.now().isoformat(),
                is_active=True
            ))
        return templates


class DatabaseConfigurationService(ConfigurationService):
    """Database-based implementation (for future use)"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        # Initialize database connection
        # This would use SQLAlchemy or similar
        raise NotImplementedError("Database implementation not yet available")
    
    # All abstract methods would need to be implemented here
    # using database operations instead of file operations