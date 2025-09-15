# Lloyds Separate Debit/Credit Columns Fix Summary

## Problem Identified

**Issue**: The amount extraction logic was not properly handling Lloyds bank statements that have separate 'debits' and 'credits' columns.

**Root Causes**:
1. **Template Inconsistency**: Upload viewmodel had `debit_positive=False` for Lloyds (incorrect)
2. **Logic Assumption**: Code assumed both debit and credit amounts could be non-zero simultaneously
3. **Missing Debug Info**: No logging to verify conversion was working correctly

## Solution Applied

### 1. Fixed Template Configuration

**File**: `viewmodels/upload_viewmodel.py`

**Change**: Corrected Lloyds template to have `debit_positive=True`
```python
BankTemplate(
    name="Lloyds Bank",
    bank_type="lloyds",
    debit_positive=True,  # Fixed: was False, now True
    # ... rest of template
)
```

### 2. Enhanced Amount Extraction Logic

**File**: `models/bank_file_processor.py`

**Key Improvements**:

1. **Proper Separate Column Handling**:
   ```python
   if self.debit_positive:
       # Lloyds format with separate debit/credit columns:
       # - Debit column: positive values (need to convert to negative)
       # - Credit column: positive values (keep as positive)
       # - Only one column will have a value, the other will be 0
       if debit_amount > 0:
           return -debit_amount  # Convert positive debit to negative
       elif credit_amount > 0:
           return credit_amount  # Keep positive credit as positive
   ```

2. **Added Debug Logging**:
   ```python
   logger.debug(f"Lloyds debit conversion: {debit_amount} -> {result}")
   logger.debug(f"Lloyds credit: {credit_amount} -> {result}")
   ```

3. **Clear Documentation**: Added comments explaining the Lloyds format expectations

## Technical Details

### Lloyds Bank Statement Format

**Typical Lloyds CSV Structure**:
```csv
Posting Date,Type,Details,Debits,Credits
11-Apr-2025,DD,PAYROLL SALARY,1000.00,
12-Apr-2025,FP,SUPPLIER PAYMENT,500.00,
13-Apr-2025,CR,REFUND RECEIVED,,250.00
```

**Key Characteristics**:
- **Debits Column**: Contains positive values for outgoing payments
- **Credits Column**: Contains positive values for incoming payments
- **Mutual Exclusivity**: Only one column has a value per row, the other is empty
- **Sign Convention**: Both columns show positive values (unlike ERP which uses negative debits)

### Conversion Logic

**Before Fix**:
- Lloyds debit: +1000.00 → +1000.00 (incorrect)
- ERP debit: -1000.00 → -1000.00
- **Result**: No match (opposite signs)

**After Fix**:
- Lloyds debit: +1000.00 → -1000.00 (converted)
- ERP debit: -1000.00 → -1000.00
- **Result**: Perfect match (same signs)

### Template Configuration

**Corrected Lloyds Template**:
```json
{
  "name": "Lloyds Bank",
  "bank_type": "lloyds",
  "debit_positive": true,  // Correctly set to true
  "column_mapping": {
    "debit": ["debits"],
    "credit": ["credits"]
  }
}
```

## Expected Results

### 1. Proper Amount Conversion
- ✅ **Lloyds debits** (+1000.00) → **ERP debits** (-1000.00) = Perfect match
- ✅ **Lloyds credits** (+250.00) → **ERP credits** (+250.00) = Perfect match
- ✅ **Consistent sign conventions** across all data sources

### 2. Improved Matching Performance
- ✅ **Higher match rates** for Lloyds bank statements
- ✅ **Reduced false negatives** due to sign convention mismatches
- ✅ **Better accuracy** in transaction reconciliation

### 3. Debug Visibility
- ✅ **Clear logging** of amount conversions
- ✅ **Easy troubleshooting** of extraction issues
- ✅ **Verification** that logic is working correctly

## Files Modified

### Core Processing
- `models/bank_file_processor.py` - Enhanced `_extract_amount` method with proper separate column handling
- `viewmodels/upload_viewmodel.py` - Fixed Lloyds template `debit_positive` setting

## Example Scenarios

### Scenario 1: Lloyds Debit Transaction
- **Bank Statement**: Debits=1000.00, Credits=0.00
- **Extraction Result**: -1000.00 (converted for ERP consistency)
- **ERP Transaction**: -1000.00 (debit)
- **Match Result**: Perfect match (100% score)

### Scenario 2: Lloyds Credit Transaction
- **Bank Statement**: Debits=0.00, Credits=250.00
- **Extraction Result**: +250.00 (no conversion needed)
- **ERP Transaction**: +250.00 (credit)
- **Match Result**: Perfect match (100% score)

### Scenario 3: Debug Logging Output
```
DEBUG - Lloyds debit conversion: 1000.0 -> -1000.0
DEBUG - Lloyds credit: 250.0 -> 250.0
```

## Summary

The Lloyds separate debit/credit columns fix ensures that:

1. **Lloyds bank statements** with separate debit/credit columns are properly processed
2. **Template configuration** is consistent across all components
3. **Amount conversion** correctly handles the mutual exclusivity of debit/credit columns
4. **Debug logging** provides visibility into the conversion process
5. **Sign conventions** are consistent with ERP data for successful matching

This fix addresses the specific format used by Lloyds bank statements where debits and credits are in separate columns, both showing positive values, requiring conversion of debits to negative values for ERP consistency.
