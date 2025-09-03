# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ================================
# training/model_factory.py
# ================================

"""Thin factory wrapper for model-related creation."""

from typing import Any, Optional

from models.ml.training.data_models import ModelTrainingConfig

class ModelFactory:
    """Factory delegating work to :class:`ModelTrainingConfig`."""
    
    @staticmethod
    def create_model(config: ModelTrainingConfig):
        """Create a model instance using the provided configuration."""
        return config.create_model()
    
    @staticmethod
    def create_scaler(config: ModelTrainingConfig) -> Optional[Any]:
        """Create a feature scaler if configured."""
        return config.create_scaler()