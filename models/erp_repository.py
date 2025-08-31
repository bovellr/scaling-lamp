# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ================================
# models/erp_repository.py
# ================================

"""
Repository for persisting ERP database configurations.
"""

from pathlib import Path
from dataclasses import asdict
from typing import List, Dict, Optional, Any
from cryptography.fernet import Fernet
import base64
import logging
import json

from .database_models import DatabaseConnection, ERPQueryTemplate


logger = logging.getLogger(__name__)

class ERPConfigurationRepository:
    """Repository for ERP database configurations with encryption."""
    
    def __init__(self, config_dir: str = "data/erp_config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.connections_file = self.config_dir / "connections.json"
        self.queries_file = self.config_dir / "queries.json"
        self.key_file = self.config_dir / ".key"
        
        self._ensure_encryption_key()
    
    def _ensure_encryption_key(self):
        """Ensure encryption key exists for password protection."""
        if not self.key_file.exists():
            try:
                key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                # Make key file read-only
                self.key_file.chmod(0o600)
            except OSError as e:
                logger.error(f"Failed to create encryption key file: {e}")
                raise
    
    def _get_cipher(self) -> Fernet:
        """Get encryption cipher for passwords."""
        try:
            with open(self.key_file, 'rb') as f:
                key = f.read()
            return Fernet(key)
        except OSError as e:
            logger.error(f"Failed to read encryption key file: {e}")
            raise
    
    def _encrypt_password(self, password: str) -> str:
        """Encrypt password for storage."""
        if not password:
            return ""
        cipher = self._get_cipher()
        encrypted = cipher.encrypt(password.encode())
        return base64.b64encode(encrypted).decode()
    
    def _decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt password from storage."""
        if not encrypted_password:
            return ""
        try:
            cipher = self._get_cipher()
            encrypted_bytes = base64.b64decode(encrypted_password.encode())
            decrypted = cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Password decryption failed: {e}")
            return ""
    
    def save_connection(self, connection: DatabaseConnection) -> bool:
        """Save database connection with encrypted password."""
        try:
            connections = self.load_connections()
 
           # Update or add connection
            connections[connection.name] = connection

            # Convert connections to dictionaries and encrypt passwords
            connections_data = {}
            for name, conn in connections.items():
                conn_dict = asdict(conn)
                if conn_dict["password"]:
                    conn_dict["password"] = self._encrypt_password(conn_dict["password"])
                connections_data[name] = conn_dict

            with open(self.connections_file, "w") as f:
                json.dump(connections_data, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Failed to save connection: {e}")
            return False
    
    def load_connections(self) -> Dict[str, DatabaseConnection]:
        """Load database connections with decrypted passwords."""
        try:
            if not self.connections_file.exists():
                return {}
            
            with open(self.connections_file, 'r') as f:
                connections_data = json.load(f)
            
            connections = {}
            for name, conn_dict in connections_data.items():
                # Decrypt password
                if conn_dict.get('password'):
                    conn_dict['password'] = self._decrypt_password(conn_dict['password'])
                
                connections[name] = DatabaseConnection(**conn_dict)
            
            return connections
        except Exception as e:
            logger.error(f"Failed to load connections: {e}")
            return {}
    
    def delete_connection(self, connection_name: str) -> bool:
        """Delete database connection."""
        try:
            connections = self.load_connections()
            if connection_name in connections:
                del connections[connection_name]
                
                # Save without the deleted connection
                connections_data = {}
                for name, conn in connections.items():
                    conn_dict = asdict(conn)
                    if conn_dict['password']:
                        conn_dict['password'] = self._encrypt_password(conn_dict['password'])
                    connections_data[name] = conn_dict
                
                with open(self.connections_file, 'w') as f:
                    json.dump(connections_data, f, indent=2)
                
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete connection: {e}")
            return False
    
    def save_query_template(self, template: ERPQueryTemplate) -> bool:
        """Save query template."""
        try:
            templates = self.load_query_templates()
            templates[template.name] = template

            templates_data = {name: asdict(tpl) for name, tpl in templates.items()}
            with open(self.queries_file, "w") as f:
                json.dump(templates_data, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Failed to save query template: {e}")
            return False
    
    def load_query_templates(self) -> Dict[str, ERPQueryTemplate]:
        """Load query templates."""
        try:
            if not self.queries_file.exists():
                return {}
            
            with open(self.queries_file, 'r') as f:
                templates_data = json.load(f)
            
            templates = {}
            for name, template_dict in templates_data.items():
                try:
                    # Validate that template_dict is actually a dictionary
                    if not isinstance(template_dict, dict):
                        logger.error(f"Invalid template data for '{name}': expected dict, got {type(template_dict)}")
                        continue
                    
                    # Convert parameter dictionaries back to QueryParameter objects
                    if 'parameters' in template_dict:
                        from .database_models import QueryParameter
                        # Validate parameters is a list
                        if not isinstance(template_dict['parameters'], list):
                            logger.error(f"Invalid parameters for template '{name}': expected list, got {type(template_dict['parameters'])}")
                            template_dict['parameters'] = []
                        else:
                            params = []
                            for param_dict in template_dict['parameters']:
                                if isinstance(param_dict, dict):
                                    try:
                                        params.append(QueryParameter(**param_dict))
                                    except Exception as e:
                                        logger.error(f"Failed to create QueryParameter from {param_dict}: {e}")
                                        continue
                                else:
                                    logger.error(f"Invalid parameter data: expected dict, got {type(param_dict)}")
                            template_dict['parameters'] = params
                    
                    # Create ERPQueryTemplate with validated data
                    templates[name] = ERPQueryTemplate(**template_dict)
                    
                except Exception as e:
                    logger.error(f"Failed to load template '{name}': {e}")
                    continue
            
            return templates
        except Exception as e:
            logger.error(f"Failed to load query templates: {e}")
            return {}
    
    def delete_query_template(self, template_name: str) -> bool:
        """Delete query template."""
        try:
            templates = self.load_query_templates()
            if template_name in templates:
                del templates[template_name]
                
                templates_data = {name: asdict(template) for name, template in templates.items()}
                with open(self.queries_file, 'w') as f:
                    json.dump(templates_data, f, indent=2)
                
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete query template: {e}")
            return False