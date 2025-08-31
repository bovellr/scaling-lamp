# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.
# ================================
# models/text_utils.py
# ================================
"""
Text utility functions for transaction processing.
"""

import re
from typing import Optional


def normalize_description(description: str, date_str: Optional[str] = None) -> str:
    """Normalize description for comparison and matching.
    
    Args:
        description: The transaction description to normalize
        date_str: Optional date string that might be embedded in description
        
    Returns:
        Normalized description string
    """
    if not description:
        return ""
    
    # Convert to lowercase and remove extra whitespace
    normalized = description.lower().strip()
    
    # Remove common punctuation and special characters
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized
