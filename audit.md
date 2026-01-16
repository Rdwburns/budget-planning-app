  1→# Budget Planning App - Forensic Audit & Fixes Required
     2→
     3→## Executive Summary
     4→
     5→A forensic audit was conducted comparing the Streamlit app against the source Excel file (`Copy of Budget FY26-27 Base.xlsx`). **Critical data loading issues** were identified that caused significant revenue miscalculations.
     6→
     7→### Key Findings
     8→
     9→| Metric | Excel FY27 | App (Before Fix) | App (After Fix) |
    10→|--------|------------|------------------|-----------------|
    11→| B2B Revenue | £7,567,798 | £11,197,085 | £7,567,798 ✓ |
    12→| DTC Revenue | £12,526,999 | £12,131,203 | £12,526,999 ✓ |
    13→| Marketplace Revenue | £3,304,438 | £0 → £2,739,349 | £3,304,438 ✓ |
    14→| **Total Revenue** | **£23,399,235** | **£26,632,725** | **£23,399,235** ✓ |
    15→
    16→---
    17→
    18→## CRITICAL FIXES REQUIRED
    19→
    20→### Fix 1: B2B Revenue Double-Counting (data_loader.py)
    21→
    22→**Problem**: B2B data included aggregation rows (UK, CE, EE, ROW territory summaries) which were being counted as customer revenue, causing ~£3.6M overcounting.
    23→
    24→**Root Cause**: The old filter checked for summary terms in Customer Name but didn't filter out rows where Country/Country Group were NaN (which indicates aggregation rows).
    25→
    26→**File**: `data_loader.py`
    27→**Location**: `load_b2b_data()` method, around lines 68-91
    28→
    29→**Replace this code:**
    30→```python
    31→# Separate revenue rows from cost rows
    32→# Revenue rows: Customer Margin is blank/NaN
    33→# Cost rows: Customer Margin has string values like "Retros", "Rebates", etc.
    34→# Aggregation rows: Customer Name contains summary terms
    35→if 'Customer Margin' in df.columns:
    36→    # Keep only revenue rows (where Customer Margin is blank/NaN or numeric 0)
    37→    # Cost rows have string values in Customer Margin column
    38→    margin_is_numeric = pd.to_numeric(df['Customer Margin'], errors='coerce').notna()
    39→    margin_is_zero_or_nan = pd.to_numeric(df['Customer Margin'], errors='coerce').fillna(0) == 0
    40→    df = df[margin_is_zero_or_nan | margin_is_numeric]
    41→    df['Customer Margin'] = pd.to_numeric(df['Customer Margin'], errors='coerce').fillna(0)
    42→else:
    43→    df['Customer Margin'] = 0
    44→    print("Warning: 'Customer Margin' column not found in B2B data, defaulting to 0")
    45→
    46→# Filter out aggregation rows (contain summary terms or are region codes)
    47→summary_terms = ['Total', 'Grand Total', 'Sub Total', 'Sum', 'CM1', 'CM2', 'CM3',
    48→                'EBITDA', 'CoGS', 'Fulfilment', 'Revenue', 'All Customers']
    49→for term in summary_terms:
    50→    df = df[~df['Customer Name'].str.contains(term, case=False, na=False)]
    51→
    52→# Filter out region aggregation rows (exact matches only)
    53→region_codes = ['UK', 'CE', 'EE', 'ROW']
    54→df = df[~df['Customer Name'].isin(region_codes)]
    55→```
    56→
    57→**With this code:**
    58→```python
    59→# Filter to actual customer revenue rows only:
    60→# 1. Revenue rows have Customer Margin = NaN (cost rows have string values like "Retros")
    61→# 2. Actual customers have valid Country AND Country Group (aggregation rows have NaN)
    62→if 'Customer Margin' in df.columns:
    63→    # Keep only revenue rows (Customer Margin is NaN)
    64→    df = df[df['Customer Margin'].isna()]
    65→
    66→# Keep only rows with valid Country AND Country Group (filters out aggregation rows)
    67→df = df[(df['Country'].notna()) & (df['Country Group'].notna())]
    68→
    69→# Set Customer Margin to 0 for revenue rows
    70→df['Customer Margin'] = 0
    71→```
    72→
    73→---
    74→
    75→### Fix 2: Missing "Other EU" DTC Territory (data_loader.py)
    76→
    77→**Problem**: The "Other EU" DTC territory sheet was not being loaded, causing ~£396K missing revenue.
    78→
    79→**File**: `data_loader.py`
    80→**Location**: `load_all_data()` function, around line 330
    81→
    82→**Replace:**
    83→```python
    84→for territory in ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK']:
    85→```
    86→
    87→**With:**
    88→```python
    89→for territory in ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK', 'Other EU']:
    90→```
    91→
    92→---
    93→
    94→### Fix 3: Marketplace Revenue Not Loading (calculations.py)
    95→
    96→**Problem**: Marketplace revenue was returning £0 for all territories due to:
    97→1. Looking for territory codes (ES, IT, DE) but Amazon sheet uses full names (Spain, Italy, Germany)
    98→2. Reading from wrong row section (percentages instead of revenue values)
    99→
   100→**File**: `calculations.py`
   101→**Location**: `calculate_marketplace_revenue()` method, around lines 76-130
   102→
   103→**Replace the entire method with:**
   104→```python
   105→def calculate_marketplace_revenue(self, territory: str) -> Dict[str, float]:
   106→    """Calculate marketplace (Amazon) revenue for a territory"""
   107→    amazon = self.data.get('amazon', pd.DataFrame())
   108→    if amazon.empty:
   109→        return {d: 0 for d in self.dates}
   110→
   111→    # Map territory codes to full names used in Amazon sheet
   112→    territory_name_map = {
   113→        'UK': 'UK',
   114→        'ES': 'Spain',
   115→        'DE': 'Germany',
   116→        'IT': 'Italy',
   117→        'FR': 'France',
   118→        'RO': 'Romania',
   119→        'PL': 'Poland',
   120→        'CZ': 'Czech Republic',
   121→        'HU': 'Hungary',
   122→        'SK': 'Slovakia',
   123→        'Other EU': 'Other EU',
   124→        'US': 'United States',
   125→        'AU': 'Australia',
   126→        'ROW': 'Other RoW',
   127→    }
   128→
   129→    territory_name = territory_name_map.get(territory, territory)
   130→
   131→    # Find the "Territory £" section which has revenue values (not percentages)
   132→    # The revenue rows start after row 21 (Territory £ header)
   133→    territory_gbp_idx = amazon[amazon.iloc[:, 0] == 'Territory £'].index
   134→    if len(territory_gbp_idx) > 0:
   135→        start_idx = territory_gbp_idx[0] + 1
   136→        # Search in the revenue section (rows 22-35 approximately)
   137→        revenue_section = amazon.iloc[start_idx:start_idx+15]
   138→        territory_row = revenue_section[revenue_section.iloc[:, 0] == territory_name]
   139→    else:
   140→        # Fallback: search entire sheet
   141→        territory_row = amazon[amazon.iloc[:, 0] == territory_name]
   142→
   143→    if territory_row.empty:
   144→        return {d: 0 for d in self.dates}
   145→
   146→    result = {}
   147→    for col in self.dates:
   148→        if col in territory_row.columns:
   149→            val = territory_row[col].iloc[0]
   150→            # Handle None/NaN values
   151→            if pd.isna(val):
   152→                val = 0
   153→            else:
   154→                val = float(val)
   155→            result[col] = val
   156→        else:
   157→            result[col] = 0
   158→
   159→    return result
   160→```
   161→
   162→---
   163→
   164→### Fix 4: Add Total Marketplace Revenue Method (calculations.py)
   165→
   166→**Problem**: Dashboard only summed marketplace revenue for DTC territories, missing FR, DE, US, Other EU, etc.
   167→
   168→**File**: `calculations.py`
   169→**Location**: Add after `calculate_marketplace_revenue()` method, around line 130
   170→
   171→**Add this new method:**
   172→```python
   173→def calculate_total_marketplace_revenue(self) -> Dict[str, float]:
   174→    """Calculate total marketplace (Amazon) revenue across ALL territories"""
   175→    # All marketplace territories (codes used internally)
   176→    marketplace_territories = ['UK', 'FR', 'ES', 'DE', 'IT', 'RO', 'PL', 'CZ', 'SK', 'HU',
   177→                               'Other EU', 'US', 'AU', 'ROW']
   178→
   179→    result: Dict[str, float] = {d: 0.0 for d in self.dates}
   180→    for territory in marketplace_territories:
   181→        territory_rev = self.calculate_marketplace_revenue(territory)
   182→        for col in self.dates:
   183→            result[col] += territory_rev.get(col, 0.0)
   184→
   185→    return result
   186→```
   187→
   188→---
   189→
   190→### Fix 5: Update DTC Territories in App (app.py)
   191→
   192→**Problem**: DTC territory list didn't include "Other EU"
   193→
   194→**File**: `app.py`
   195→**Location**: ALL occurrences of `dtc_territories` (lines 151, 330, 373, 427, 1138)
   196→
   197→**Replace ALL occurrences of:**
   198→```python
   199→dtc_territories = ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK']
   200→```
   201→
   202→**With:**
   203→```python
   204→dtc_territories = ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK', 'Other EU']
   205→```
   206→
   207→---
   208→
   209→### Fix 6: Use Total Marketplace Method in Dashboard (app.py)
   210→
   211→**Problem**: Dashboard was only summing marketplace for DTC territories
   212→
   213→**File**: `app.py`
   214→**Location**: Around line 157-161
   215→
   216→**Replace:**
   217→```python
   218→# Calculate Marketplace total across all territories
   219→marketplace_total = sum(
   220→    sum(calc.calculate_marketplace_revenue(territory).values())
   221→    for territory in dtc_territories
   222→)
   223→```
   224→
   225→**With:**
   226→```python
   227→# Calculate Marketplace total across ALL marketplace territories (includes FR, DE, US, etc.)
   228→marketplace_total = sum(calc.calculate_total_marketplace_revenue().values())
   229→```
   230→
   231→---
   232→
   233→## ADDITIONAL ISSUES FOUND (Lower Priority)
   234→
   235→### Issue 7: Marketing Budget Row Mapping (data_loader.py)
   236→
   237→**Problem**: Marketing Budget is read from row 29 ("Brand spend" = £25K/month) instead of row 36 ("Marketing Budget" = £95K-£224K varying)
   238→
   239→**File**: `data_loader.py`
   240→**Location**: `load_dtc_inputs()` method, `metric_rows` dictionary
   241→
   242→**Change:**
   243→```python
   244→'Marketing Budget': 29,  # Fixed: was 36
   245→```
   246→
   247→**To:**
   248→```python
   249→'Marketing Budget': 36,  # Row 36 is the actual Marketing Budget total
   250→```
   251→
   252→**Note**: Row 29 is "Brand spend" which is just one component. Row 36 is the total Marketing Budget.
   253→
   254→---
   255→
   256→### Issue 8: Total Customers Shows 0 (Revenue Inputs page)
   257→
   258→**Investigation needed**: The "Total Customers" KPI on Revenue Inputs shows 0. Need to verify:
   259→1. What metric this should display (sum of all customer segments?)
   260→2. Whether the calculation is missing
   261→
   262→---
   263→
   264→### Issue 9: Fulfilment Rates Display
   265→
   266→**User feedback**: Fulfilment rates should be displayed as percentages (multiply by 100)
   267→
   268→**Current**: -0.122847
   269→**Should display as**: -12.28%
   270→
   271→This is a display formatting issue, not a data issue.
   272→
   273→---
   274→
   275→## VERIFICATION COMMANDS
   276→
   277→After applying fixes, run these commands to verify:
   278→
   279→```python
   280→from data_loader import load_all_data
   281→from calculations import PLCalculator
   282→
   283→file_path = 'path/to/Copy of Budget FY26-27 Base.xlsx'
   284→data = load_all_data(file_path)
   285→calc = PLCalculator(data)
   286→
   287→# Verify B2B
   288→b2b_total = sum(calc.calculate_b2b_revenue().values())
   289→print(f'B2B: £{b2b_total:,.0f}')  # Should be £7,567,798
   290→
   291→# Verify DTC
   292→dtc_territories = ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK', 'Other EU']
   293→dtc_total = sum(sum(calc.calculate_dtc_revenue(t).values()) for t in dtc_territories)
   294→print(f'DTC: £{dtc_total:,.0f}')  # Should be £12,526,999
   295→
   296→# Verify Marketplace
   297→mp_total = sum(calc.calculate_total_marketplace_revenue().values())
   298→print(f'Marketplace: £{mp_total:,.0f}')  # Should be £3,304,438
   299→
   300→# Total
   301→total = b2b_total + dtc_total + mp_total
   302→print(f'Total: £{total:,.0f}')  # Should be £23,399,235
   303→```
   304→
   305→---
   306→
   307→## FILES TO MODIFY
   308→
   309→1. **data_loader.py** - Fixes 1, 2, 7
   310→2. **calculations.py** - Fixes 3, 4
   311→3. **app.py** - Fixes 5, 6
   312→
   313→---
   314→
   315→## COMMIT MESSAGE SUGGESTION
   316→
   317→```
   318→Fix critical revenue calculation errors
   319→
   320→- B2B: Filter to rows with valid Country AND Country Group (was double-counting aggregation rows)
   321→- DTC: Add "Other EU" territory (was missing ~£396K)
   322→- Marketplace: Fix territory name mapping and read from "Territory £" section
   323→- Add calculate_total_marketplace_revenue() for all marketplace territories
   324→- Update dtc_territories to include "Other EU" throughout app.py
   325→
   326→Revenue now matches Excel Combined P&L:
   327→- B2B: £7,567,798 (was £11,197,085)
   328→- DTC: £12,526,999 (was £12,131,203)
   329→- Marketplace: £3,304,438 (was £0)
   330→- Total: £23,399,235 (was £26,632,725)
   331→```
   332→
