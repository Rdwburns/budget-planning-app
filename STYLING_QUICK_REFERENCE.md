# Dataframe Styling - Quick Reference Card

## ✅ YES, You Can Format Dataframe Rows!

The Budget Planning App now has **comprehensive row and cell-level formatting** using pandas Styler.

---

## Quick Examples

### 1. Already Implemented: Dashboard Top 10 Customers

```python
# Green gradient + bold top 3 + currency formatting
def style_top_customers(df):
    styled = df.style
    styled = styled.background_gradient(subset=['Total Revenue'], cmap='Greens')
    styled = styled.format({'Total Revenue': '£{:,.0f}'})
    # Bold top 3 customers
    def bold_top_3(s):
        is_top_3 = [True if i < 3 else False for i in range(len(s))]
        return ['font-weight: bold' if v else '' for v in is_top_3]
    styled = styled.apply(bold_top_3, axis=0)
    return styled
```

**Result**:
- Revenue column has green gradient (darker = higher)
- Top 3 rows are bold
- All values formatted as £1,234,567

---

## 2. Color Rows by Region

```python
from dataframe_styles import color_by_category

styled = color_by_category(df, 'Country Group')
st.dataframe(styled)
```

**Result**: UK=blue, CE=orange, EE=purple, ROW=green rows

---

## 3. Highlight Top Performers

```python
from dataframe_styles import highlight_top_n

styled = highlight_top_n(df, value_col='Total Revenue', n=5, color='#ffd700')
st.dataframe(styled)
```

**Result**: Top 5 rows highlighted in gold

---

## 4. Traffic Light Coloring

```python
from dataframe_styles import apply_thresholds

styled = apply_thresholds(df, 'Revenue', [
    (1000000, '#198754'),  # >1M = green
    (500000, '#ffc107'),   # >500K = yellow
    (0, '#dc3545')         # <500K = red
])
```

**Result**: Revenue cells colored by performance threshold

---

## 5. Comprehensive B2B Styling

```python
from dataframe_styles import comprehensive_b2b_style

styled = comprehensive_b2b_style(b2b_df)
st.dataframe(styled, width='stretch')
```

**Result**: Currency + gradient + negative highlighting + borders

---

## Available Functions in `dataframe_styles.py`

| Function | Purpose | Example Use |
|----------|---------|-------------|
| `style_currency_table()` | Format £ + gradient | Revenue tables |
| `highlight_top_n()` | Highlight top rows | Top customers |
| `color_by_category()` | Color by region/status | Regional data |
| `highlight_negative_values()` | Red for negatives | Margins, P&L |
| `highlight_zero_values()` | Highlight zeros/blanks | Missing data |
| `zebra_stripes()` | Alternating rows | Long tables |
| `apply_thresholds()` | Traffic lights | KPIs, targets |
| `comprehensive_b2b_style()` | All-in-one B2B | Customer tables |

---

## Common Patterns

### Pattern 1: Currency + Gradient
```python
styled = style_currency_table(
    df,
    currency_cols=['Revenue', 'Cost'],
    gradient_col='Revenue'
)
```

### Pattern 2: Color by Status
```python
styled = color_by_category(df, 'Status', {
    'Active': '#d4edda',
    'Pending': '#fff3cd',
    'Inactive': '#f8d7da'
})
```

### Pattern 3: Bold Totals in P&L
```python
def bold_totals(row):
    if 'Total' in str(row.name) or 'EBITDA' in str(row.name):
        return ['font-weight: bold; background-color: #f5f5f5'] * len(row)
    return [''] * len(row)

styled = df.style.apply(bold_totals, axis=1)
```

---

## Color Reference

| Color | Hex | Use Case |
|-------|-----|----------|
| 🟢 Green | `#d4edda` | Success, positive variance |
| 🔴 Red | `#f8d7da` | Errors, negative variance |
| 🟡 Yellow | `#fff3cd` | Warnings, pending |
| 🔵 Blue | `#e3f2fd` | UK region, info |
| 🟠 Orange | `#fff3e0` | CE region |
| 🟣 Purple | `#f3e5f5` | EE region |
| 🟩 Light Green | `#e8f5e9` | ROW region |
| 🟨 Gold | `#ffd700` | Top performers |

---

## Where to Use

### Dashboard
- ✅ **Top 10 Customers**: Green gradient + bold top 3 (IMPLEMENTED)
- 🔄 Regional Revenue: Blue gradient by region
- 🔄 Monthly Trends: Heat map for revenue patterns

### B2B Management
- 🔄 Customer List: Color by region
- 🔄 Margin Column: Highlight negatives in red
- 🔄 Total Column: Green gradient

### P&L View
- 🔄 Total Rows: Bold + gray background
- 🔄 Costs: Red text
- 🔄 Revenue: Green text

### Scenario Planning
- 🔄 Variance: Red/green by sign
- 🔄 Comparison Table: Highlight changes

---

## Full Documentation

- **[STYLING_GUIDE.md](STYLING_GUIDE.md)** - Complete guide with examples
- **[dataframe_styles.py](dataframe_styles.py)** - Source code with all functions
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - All recent improvements

---

## Requirements

✅ matplotlib>=3.7.0 (added to requirements.txt)
✅ pandas>=2.0.0 (already installed)
✅ All dependencies installed and working

---

## Current Status

**App Running**: http://localhost:8501
**Deployed**: Pushed to GitHub (auto-deploys to Streamlit Cloud)
**Commit**: 11ba530

**Features Live**:
- ✅ Green gradient on Top 10 Customers
- ✅ Bold formatting for top 3
- ✅ Currency formatting throughout
- ✅ Reusable styling module ready to use
- ✅ Comprehensive documentation

---

## Next Steps

Want to add more styling? Just import and use:

```python
from dataframe_styles import [function_name]

styled = [function_name](your_df, ...)
st.dataframe(styled, width='stretch')
```

All functions are documented in [STYLING_GUIDE.md](STYLING_GUIDE.md)!
