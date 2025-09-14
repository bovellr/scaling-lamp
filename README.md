# Bank Reconciliation AI

[![Build Status](https://github.com/yourorg/bank_reconciliation_ai/actions/workflows/build.yml/badge.svg)](https://github.com/yourorg/bank_reconciliation_ai/actions/workflows/build.yml)
[![Test Status](https://github.com/yourorg/bank_reconciliation_ai/actions/workflows/test.yml/badge.svg)](https://github.com/yourorg/bank_reconciliation_ai/actions/workflows/test.yml)

Bank Reconciliation AI is a desktop application that leverages machine learning to match bank statements with ERP ledger entries. Built with Python and PySide6, it provides an interactive interface and modular architecture to streamline financial reconciliation.

## Installation

```bash
git clone <repository-url>
cd bank_reconciliation_ai
make setup  # install dependencies and bootstrap project
# or
pip install -r requirements.txt
```

## Architecture Overview

- **`main.py`** – application entry point launching the PySide6 GUI.
- **`config/`** – configuration and persistent settings management.
- **`services/`** – shared services such as logging and an event bus for decoupled communication.
- **`models/`** – data models, machine learning engine and repository helpers.
- **`views/` & `viewmodels/`** – UI components following an MVVM-style pattern.
- **`resources/`** – static assets including stylesheets.

## Examples

Launch the GUI application:

```bash
python main.py
```

Use the machine learning engine programmatically:

```python
from models.data_models import BankTransaction, ERPTransaction
from models.ml_engine import MLEngine
import logging
import pandas as pd

logger = logging.getLogger(__name__)

bank = [BankTransaction(id="1", amount=100.0, date=pd.Timestamp("2024-01-01"), description="Payment")]
erp = [ERPTransaction(id="2", amount=100.0, date=pd.Timestamp("2024-01-01"), description="Customer payment")]

engine = MLEngine()
matches = engine.generate_matches(bank, erp)
for match in matches:
    logger.info(match.confidence_score)
```

## Documentation

- [User Guide](USER_GUIDE.md)
- [Full Documentation](docs/README.md)
