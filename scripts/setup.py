    #!/usr/bin/env python3
"""Quick setup script for Bank Reconciliation AI"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and print the result"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
        else:
            print(f"❌ {description} failed")
            print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False
    return True

def main():
    """Run the setup process"""
    print("🚀 Setting up Bank Reconciliation AI...")
    print()
    
    if not Path("main.py").exists():
        print("❌ Please run this script from the bank_reconciliation_ai directory")
        sys.exit(1)
    
    # Install dependencies
    run_command("pip install -r requirements.txt", "Installing dependencies")
    
    # Create sample data
    print("📊 Creating sample data...")
    
    sample_bank_data = """Amount,Date,Description
100.00,2024-01-01,Payment to ABC Corp
-50.00,2024-01-02,ATM Withdrawal Main St
200.00,2024-01-03,Salary Credit
75.50,2024-01-04,Grocery Store Purchase
-25.00,2024-01-05,Coffee Shop
150.00,2024-01-06,Freelance Payment
-120.00,2024-01-07,Utility Bill Payment"""
    
    with open("data/sample_bank.csv", "w") as f:
        f.write(sample_bank_data)
    
    sample_erp_data = """Amount,Date,Description
100.00,2024-01-01,ABC Corporation Invoice
200.00,2024-01-03,Monthly Salary
80.00,2024-01-05,Grocery Chain Payment
-45.00,2024-01-02,Cash Withdrawal
150.00,2024-01-06,Contract Payment
-125.00,2024-01-07,Electric Company"""
    
    with open("data/sample_erp.csv", "w") as f:
        f.write(sample_erp_data)
    
    print("✅ Sample data created")
    print()
    print("🎉 Setup completed successfully!")
    print()
    print("Next steps:")
    print("1. Activate your virtual environment: source venv/bin/activate")
    print("2. Run the application: python main.py")
    print("3. Test the setup: python tests/test_basic.py")
    print()

if __name__ == "__main__":
    main()
