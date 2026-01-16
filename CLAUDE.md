# Budget Planning & Forecasting App

## Overview
A Streamlit-based web application for FY26-27 budget management, planning, and forecasting. This app provides comprehensive tools for managing B2B customer data, DTC revenue inputs, cost management, and scenario planning.

## Architecture

### Core Components

**app.py** - Main Streamlit application
- Page routing and navigation
- UI rendering for all views
- File upload handling with state management
- Custom CSS styling for enhanced UX

**data_loader.py** - Data loading and management
- `BudgetDataLoader` class for Excel file processing
- Sheet-specific loaders for B2B, DTC, overheads, payroll, and fulfilment data
- Data validation and cleaning

**calculations.py** - Business logic and calculations
- `PLCalculator` class for P&L statement generation
- Revenue calculations (B2B, DTC, Marketplace)
- Cost calculations (CoGS, fulfilment, marketing, overheads)
- Margin calculations (CM1, CM2, EBITDA)
- Scenario modeling support

## Features

### 1. Dashboard (📊)
- Real-time KPI metrics (B2B revenue, customer count, territories, overheads)
- B2B revenue by region breakdown
- Monthly revenue trends
- Top 10 customer analysis

### 2. Revenue Inputs (💰)
- Territory-specific DTC revenue management
- Editable metrics for traffic, conversion rates, AOV
- Quick adjustment sliders for scenario modeling
- Projected impact calculations

### 3. B2B Management (📦)
- Customer forecast management
- Multi-filter support (region, search, minimum revenue)
- Editable customer data with dynamic rows
- Add new customer functionality

### 4. Cost Management (💸)
- **Overheads**: Territory and function-based filtering
- **Payroll**: Department-level view (read-only)
- **Fulfilment**: Editable rate management

### 5. Scenario Planning (🎯)
- Create and compare business scenarios
- Adjustable parameters:
  - Revenue drivers (DTC, B2B, Marketplace growth)
  - Margin impacts (CoGS, fulfilment rate changes)
  - Cost assumptions (marketing, overhead changes)
- Real-time scenario comparison
- Save and load scenarios

### 6. P&L View (📈)
- Full profit & loss statement generation
- Multiple view modes: Combined, By Territory, By Channel
- Monthly, Quarterly, Annual aggregation
- Key metrics dashboard

### 7. Export (⬇️)
- Excel export functionality
- Selective data export options
- Formula preservation option
- Timestamped file generation

## Data Structure

The app expects an Excel file with the following sheets:

- **B2B**: Customer-level revenue forecasts with columns:
  - Customer Name, Country, Country Group, Customer Margin
  - Monthly revenue columns (date format: 2026-01-01, etc.)

- **DTC**: Territory-specific metrics (UK, ES, IT, RO, CZ, HU, SK)
  - Traffic, conversion rates, AOV, returns
  - Monthly columns for forecasting

- **Overheads**: Operating expenses
  - Territory, Function, Category, Supplier
  - Monthly cost columns

- **Payroll**: Employee costs by department

- **Fulfilment**: Fulfillment rate assumptions by territory

## Key Technical Patterns

### Session State Management
The app uses Streamlit's session state to prevent infinite reload loops:
```python
file_id = f"{uploaded_file.name}_{uploaded_file.size}"
if st.session_state.get('loaded_file_id') != file_id:
    # Only process new files
    st.session_state.data = load_all_data(str(temp_path))
    st.session_state.file_loaded = True
    st.session_state.loaded_file_id = file_id
    st.rerun()
```

### Data Loading Pattern
```python
# Centralized data loading in session state
if 'data' not in st.session_state:
    default_path = Path(__file__).parent.parent / "Copy of Budget FY26-27 Base.xlsx"
    st.session_state.data = load_all_data(str(default_path))
```

### Calculator Pattern
The `PLCalculator` class supports scenario modeling through parameter overrides:
```python
calc = PLCalculator(data, scenario_params)
pl = calc.calculate_territory_pl('UK')
```

## Development

### Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

### File Upload Handling
The app uses a temporary file approach for uploaded data:
1. User uploads file via sidebar
2. File is written to `/tmp/budget_upload.xlsx`
3. Data is loaded into session state
4. File ID tracking prevents reprocessing

## Recent Fixes

### IndentationError Fix (2026-01-16)
Fixed incorrect indentation in file upload handling (lines 118-120) that caused:
- Python syntax error
- Infinite refresh loop on file upload
- App failure on Streamlit Cloud

**Solution**: Moved session state updates inside the `if file_id != loaded_file_id` block to only execute on new file uploads.

## Deployment

The app is deployed on Streamlit Cloud:
- Repository: https://github.com/Rdwburns/budget-planning-app
- Auto-deploys on push to main branch
- Requires Python 3.8+

## Known Issues & Limitations

1. **No default data file**: App requires file upload if default Excel file not present
2. **Read-only payroll**: Payroll data is view-only
3. **Limited validation**: Minimal input validation on editable fields
4. **No persistence**: Changes are session-only, not saved back to Excel automatically
5. **Single user**: No multi-user collaboration features

## Future Enhancements

- Database backend for persistent storage
- User authentication and role-based access
- Real-time collaboration
- More sophisticated scenario comparison
- Chart/visualization improvements
- Export to multiple formats (CSV, PDF)
- Automated data validation and error checking
