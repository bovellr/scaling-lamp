# Bank Reconciliation AI

Intelligent bank reconciliation application with machine learning capabilities.

## 🚀 Quick Start

### 1. Setup the project:
```bash
# Complete setup (recommended)
make setup

# Or manual setup:
python scripts/setup.py
```

### 2. Run the application:
```bash
# Using make
make run

# Or directly
python main.py
```

### 3. Test the setup:
```bash
make test
```

## 📁 Project Structure

```
bank_reconciliation_ai/
├── main.py                     # Application entry point
├── requirements.txt            # Dependencies
├── Makefile                    # Build commands
├── config/                     # Configuration
│   ├── settings.py             # App settings
│   └── constants.py            # Constants
├── views/                      # UI components
│   ├── main_window.py          # Main window
│   └── widgets/                # UI widgets
|   └── dialogs/                # Dialogs
|       └── dialog_manager.py         # Dialog manager
|       └── settings/
|           └── threshold_dialog.py   # Oracle connection dialog
|           └── oracle_dialog.py      # Oracle connection dialog
├── services/                         # Supporting services
│   ├── event_bus.py                  # Event system
│   └── logging_service.py            # Logging
├── resources/                        # Static resources
│   └── styles/                       # Stylesheets
├── data/                             # Data files
├── logs/                             # Log files
├── output/                           # Generated reports
└── tests/                            # Test files
```

## 🛠️ Available Commands

- `make setup` - Complete project setup
- `make run` - Run the application
- `make test` - Run tests
- `make clean` - Clean generated files
- `make install` - Install dependencies

## 📊 Sample Data

Sample bank and ERP transaction files are created in the `data/` directory:
- `data/sample_bank.csv` - Sample bank statement
- `data/sample_erp.csv` - Sample ERP transactions

## 🧪 Testing

Run tests to verify everything is working:
```bash
python tests/test_basic.py
```

## 📝 Development

1. **File Upload**: Upload bank and ERP transaction files
2. **Matching**: AI-powered transaction matching (coming soon)
3. **Review**: Manual review and correction (coming soon)
4. **Reports**: Generate reconciliation reports (coming soon)

## 🎯 Next Steps

After running the basic setup:

1. **Run the application** to test the file upload functionality
2. **Upload sample data** from the `data/` directory
3. **Extend functionality** by implementing the MVVM components
4. **Add ML matching** using the existing codebase patterns

## 🔧 Troubleshooting

### Common Issues:

1. **Import errors**: Make sure you're in the correct directory and ran `make setup`
2. **Qt Designer not found**: Install Qt Creator or Designer separately
3. **Missing dependencies**: Run `make install` or `pip install -r requirements.txt`

### Getting Help:

1. Check the logs in `logs/` directory
2. Run tests to verify setup: `make test`
3. Ensure all required files exist (see test_basic.py)

## 📈 Features

- ✅ **Project Structure**: Complete MVVM architecture
- ✅ **File Upload**: Drag & drop support for CSV/Excel
- ✅ **Configuration**: Persistent settings management
- ✅ **Logging**: Comprehensive logging system
- ✅ **Styling**: Modern Qt stylesheet
- ⏳ **ML Matching**: AI-powered transaction matching (in progress)
- ⏳ **Manual Review**: Human-in-the-loop corrections (in progress)
- ⏳ **Reports**: Excel/PDF report generation (in progress)
- ⏳ **Self-Learning**: Model improvement from feedback (in progress)

---

**Ready to get started?** Run `make setup` and then `make run`!
