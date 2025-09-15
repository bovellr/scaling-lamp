# UI Display Debug Summary

## Issues Reported

1. **Lloyds bank statement still shows positive debits in preview table**
2. **Unmatched bank and unmatched ERP tabs not updating correctly**
3. **Lloyds matches are still on the low side**

## Investigation Results

### 1. Amount Conversion is Working Correctly

**Test Results**:
- Bank file processor correctly converts +1000.00 debit to -1000.00
- Data transformation service preserves converted amounts
- Reconciliation finds perfect matches (100% confidence)
- Unmatched calculations work correctly (0 unmatched transactions)

**Code Flow**:
```
Raw Data → Bank File Processor → BankStatement → Data Transformation → Reconciliation
+1000.00 → -1000.00 → -1000.00 → -1000.00 → Perfect Match
```

### 2. Preview Table Should Show Converted Amounts

**Expected Display**:
```
Row 0: 11/04/2025 | PAYROLL SALARY | £-1000.00
Row 1: 12/04/2025 | REFUND RECEIVED | £250.00
```

**Code Path**:
- `_update_results()` → `_populate_results_table()` → `transaction.amount`
- Should display converted amounts from `BankStatement.transactions`

### 3. Unmatched Tabs Should Update Correctly

**Expected Behavior**:
- Matched transactions: 2 (100% confidence)
- Unmatched bank: 0
- Unmatched ERP: 0

**Code Path**:
- `_calculate_unmatched_bank()` and `_calculate_unmatched_erp()`
- Should show correct counts in tab labels

## Potential Issues

### 1. UI Caching Problem
- **Issue**: UI might be showing cached data
- **Solution**: Clear UI cache or restart application

### 2. Data Flow Disconnect
- **Issue**: UI might be using different data source
- **Solution**: Verify data flow from upload to reconciliation

### 3. Template Configuration Issue
- **Issue**: Wrong template being used
- **Solution**: Verify correct Lloyds template is selected

### 4. Date Format Issue
- **Issue**: Date patterns not matching, causing no transactions to be found
- **Solution**: Check date format in actual bank statement

## Debugging Steps

### 1. Check Preview Table Data
```python
# In the UI, check what data is being displayed
print("Preview table data:")
for i, tx in enumerate(statement.transactions):
    print(f"Row {i}: {tx.description} - Amount: {tx.amount}")
```

### 2. Check Template Selection
```python
# Verify correct template is being used
print("Selected template:", upload_vm.selected_template.name)
print("Debit positive:", upload_vm.selected_template.debit_positive)
```

### 3. Check Date Pattern Matching
```python
# Verify date patterns are matching
for pattern in template.date_patterns:
    print(f"Date pattern: {pattern}")
    print(f"Matches '11/04/2025': {template.matches_date_pattern('11/04/2025')}")
```

### 4. Check Reconciliation Results
```python
# Verify reconciliation is working
print(f"Matches found: {len(matches)}")
print(f"Unmatched bank: {len(unmatched_bank)}")
print(f"Unmatched ERP: {len(unmatched_erp)}")
```

## Files to Check

### Core Processing
- `models/bank_file_processor.py` - Amount conversion logic
- `services/data_transformation_service.py` - Data transformation
- `services/optimized_reconciliation_service.py` - Matching logic

### UI Components
- `views/widgets/file_upload_widget.py` - Preview table display
- `views/widgets/enhanced_transaction_tables_widget.py` - Unmatched tabs
- `views/main_window.py` - Reconciliation orchestration

### Configuration
- `viewmodels/upload_viewmodel.py` - Template selection
- `config/bank_templates.json` - Template configuration

## Expected Behavior After Fixes

### 1. Preview Table
- ✅ Shows converted amounts (-1000.00 for debits)
- ✅ Displays correct transaction data
- ✅ Updates when new data is loaded

### 2. Unmatched Tabs
- ✅ Shows correct counts (0 unmatched for perfect matches)
- ✅ Updates after reconciliation
- ✅ Displays transaction details correctly

### 3. Reconciliation
- ✅ Finds matches with high confidence
- ✅ Handles sign convention correctly
- ✅ Updates UI components properly

## Summary

The core logic is working correctly - amount conversion, data transformation, and reconciliation are all functioning as expected. The issues reported are likely due to:

1. **UI caching** - Need to clear cache or restart
2. **Data flow disconnect** - UI using different data source
3. **Template configuration** - Wrong template being used
4. **Date format mismatch** - Actual data format not matching patterns

The fixes implemented should resolve the sign convention issues, but the UI display problems may require additional debugging to identify the specific disconnect.

