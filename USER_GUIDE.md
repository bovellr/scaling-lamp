# Bank Reconciliation AI User Manual

## Overview

Bank Reconciliation AI streamlines the matching of bank statements with ERP ledger
transactions. The application imports data from both sources, applies configurable
matching thresholds, and produces reports to resolve discrepancies.

## Getting Started

### Launching the Application

1. Install the required dependencies:
   ```bash
   pip install -r requirements/desktop.txt
   ```
2. Start the application:
   ```bash
   python main.py
   ```

## Uploading Data

### Bank Statement
1. Click **Upload Bank Statement** and choose a CSV or Excel file.
2. If the format is new, create a template to map columns using the **Template Editor**.
3. The imported data appears in the bank statement table.

### ERP Ledger
1. Click **Upload ERP Ledger** and select the ledger export file.
2. Configure connection details via **Settings → Oracle Connection** if needed.
3. The ERP data table updates to show loaded transactions.

## Running Reconciliation

1. Ensure both bank and ERP datasets are loaded—the **Auto Reconcile** button
   becomes enabled once both sources are available.
2. Click **Auto Reconcile** to start matching transactions based on the current
   thresholds.
3. Review the results and export reports as required.

## Configuring Settings

### Thresholds
Adjust confidence thresholds under **Settings → Thresholds**. Changes are saved
and applied immediately.

### Oracle Connection
Maintain database credentials through **Settings → Oracle Connection** for reuse
across sessions.

### Account Configuration
Manage account-level preferences in **Settings → Account Settings**.

## Training and Review

Use the **Training** view to supply confirmed matches that improve the model.
Review pending matches in the **Review** tab before finalizing.

## Troubleshooting

- If a dialog fails to open, ensure the corresponding module exists in the
  `views/dialogs` directory.
- For missing data warnings, verify that both upload widgets show loaded files.
- Consult the application logs for additional diagnostic information.
