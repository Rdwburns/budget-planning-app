# Dataframe Styling Guide
**Budget Planning App - Row & Cell Formatting**

## Overview

The app now supports comprehensive row and cell-level formatting using pandas Styler and the `dataframe_styles.py` module.

---

## Quick Start

### 1. Import Styling Functions

```python
from dataframe_styles import (
    style_currency_table,
    highlight_top_n,
    color_by_category,
    comprehensive_b2b_style,
    style_dashboard_customers,
    zebra_stripes
)
```

### 2. Apply to Any DataFrame

```python
# Simple currency formatting with gradient
styled_df = style_currency_table(
    df,
    currency_cols=['Revenue', 'Cost'],
    gradient_col='Revenue'
)
st.dataframe(styled_df)
```

---

## Available Styling Functions

### 1. `style_currency_table(df, currency_cols, gradient_col=None)`

**Purpose**: Format currency columns with optional gradient

**Parameters**:
- `df`: DataFrame to style
- `currency_cols`: List of columns to format as £
- `gradient_col`: Optional column for green gradient

**Example**:
```python
styled = style_currency_table(
    top_customers,
    currency_cols=['Total Revenue', 'Customer Margin'],
    gradient_col='Total Revenue'
)
```

**Result**: £1,000,000 formatting with green gradient on Total Revenue

---

### 2. `highlight_top_n(df, value_col, n=3, color='#ffd700')`

**Purpose**: Highlight top N rows

**Parameters**:
- `value_col`: Column to rank by
- `n`: Number of rows to highlight (default 3)
- `color`: Background color (default gold)

**Example**:
```python
styled = highlight_top_n(
    customers_df,
    value_col='Total Revenue',
    n=5,
    color='#d4edda'  # Light green
)
```

**Result**: Top 5 customers highlighted in light green

---

### 3. `color_by_category(df, category_col, color_map=None)`

**Purpose**: Color entire rows based on category values

**Parameters**:
- `category_col`: Column containing categories
- `color_map`: Dict mapping values to colors

**Example**:
```python
# Default colors for Country Groups
styled = color_by_category(b2b_df, 'Country Group')

# Custom colors
styled = color_by_category(
    status_df,
    'Status',
    color_map={
        'Active': '#d4edda',
        'Pending': '#fff3cd',
        'Inactive': '#f8d7da'
    }
)
```

**Result**:
- UK rows: Light blue
- CE rows: Light orange
- EE rows: Light purple
- ROW rows: Light green

---

### 4. `highlight_negative_values(df, cols)`

**Purpose**: Highlight negative numbers in red

**Parameters**:
- `cols`: List of columns to check

**Example**:
```python
styled = highlight_negative_values(
    pl_df,
    cols=['Customer Margin', 'EBITDA', 'Total']
)
```

**Result**: Negative values appear in bold red

---

### 5. `highlight_zero_values(df, cols, color='#f8d7da')`

**Purpose**: Highlight zero or missing values

**Example**:
```python
styled = highlight_zero_values(
    revenue_df,
    cols=['2026-01', '2026-02', '2026-03']
)
```

**Result**: Zero revenue months highlighted in light red

---

### 6. `zebra_stripes(df, even_color='#f9f9f9', odd_color='#ffffff')`

**Purpose**: Alternating row colors for readability

**Example**:
```python
styled = zebra_stripes(long_table_df)
```

**Result**: Even rows light gray, odd rows white

---

### 7. `apply_thresholds(df, col, thresholds)`

**Purpose**: Color cells based on value ranges

**Parameters**:
- `thresholds`: List of (value, color) tuples

**Example**:
```python
styled = apply_thresholds(
    performance_df,
    'Revenue',
    thresholds=[
        (1000000, '#198754'),  # >1M = dark green
        (500000, '#20c997'),   # >500K = green
        (100000, '#ffc107'),   # >100K = yellow
        (0, '#dc3545')         # <100K = red
    ]
)
```

**Result**: Traffic light coloring based on revenue thresholds

---

### 8. `comprehensive_b2b_style(df)`

**Purpose**: Pre-configured styling for B2B customer tables

**Features**:
- Currency formatting on all money columns
- Gradient on Total column
- Red highlighting for negative margins
- Zebra striping
- Right-aligned numbers with borders

**Example**:
```python
styled = comprehensive_b2b_style(b2b_customers_df)
st.dataframe(styled, width='stretch')
```

---

## Real-World Examples

### Example 1: Dashboard Top 10 Customers

**Current Implementation** (already in app):

```python
def style_top_customers(df):
    styled = df.style

    # Green gradient on revenue
    styled = styled.background_gradient(
        subset=['Total Revenue'],
        cmap='Greens',
        vmin=df['Total Revenue'].min(),
        vmax=df['Total Revenue'].max()
    )

    # Format as currency
    styled = styled.format({'Total Revenue': '£{:,.0f}'})

    # Bold top 3
    def bold_top_3(s):
        is_top_3 = [True if i < 3 else False for i in range(len(s))]
        return ['font-weight: bold' if v else '' for v in is_top_3]

    styled = styled.apply(bold_top_3, axis=0)

    return styled

st.dataframe(style_top_customers(top_customers), width='stretch')
```

**What it does**:
- ✅ Shows revenue with green gradient (darker = higher)
- ✅ Formats numbers as £1,234,567
- ✅ Makes top 3 customers bold

---

### Example 2: Regional Revenue with Colors

```python
def style_regional_breakdown(df):
    styled = df.style

    # Color by region
    region_colors = {
        'UK': 'background-color: #e3f2fd',
        'CE': 'background-color: #fff3e0',
        'EE': 'background-color: #f3e5f5',
        'ROW': 'background-color: #e8f5e9'
    }

    def color_regions(row):
        color = region_colors.get(row['Region'], '')
        return [color] * len(row)

    styled = styled.apply(color_regions, axis=1)
    styled = styled.format({'Revenue': '£{:,.0f}'})

    return styled
```

---

### Example 3: P&L Statement with Conditional Formatting

```python
def style_pl_statement(df):
    styled = df.style

    # Bold total rows
    def bold_totals(row):
        row_name = str(row.name)
        if any(term in row_name for term in ['Total', 'EBITDA', 'CM1', 'CM2']):
            return ['font-weight: bold; background-color: #f8f9fa'] * len(row)
        return [''] * len(row)

    styled = styled.apply(bold_totals, axis=1)

    # Color negative values (costs) in red
    def color_by_value(val):
        if isinstance(val, str):
            if val.startswith('(£'):  # Negative values formatted as (£123)
                return 'color: #dc3545'  # Red
            elif val.startswith('£') and val != '£0':
                return 'color: #198754'  # Green for positive
        return ''

    styled = styled.applymap(color_by_value)

    return styled
```

---

### Example 4: B2B Management with Multiple Styles

```python
def style_b2b_table(df):
    styled = df.style

    # 1. Currency formatting
    currency_cols = ['Customer Margin'] + [c for c in df.columns if c.startswith('202')]
    format_dict = {col: '£{:,.0f}' for col in currency_cols if col in df.columns}
    styled = styled.format(format_dict)

    # 2. Color by region
    region_colors = {
        'UK': '#e3f2fd', 'CE': '#fff3e0',
        'EE': '#f3e5f5', 'ROW': '#e8f5e9'
    }

    def color_by_group(row):
        color = region_colors.get(row['Country Group'], '')
        return [f'background-color: {color}'] * len(row)

    styled = styled.apply(color_by_group, axis=1)

    # 3. Highlight negative margins
    def highlight_negative(val):
        if pd.notna(val) and isinstance(val, (int, float)) and val < 0:
            return 'color: red; font-weight: bold; background-color: #fff0f0'
        return ''

    styled = styled.applymap(highlight_negative, subset=['Customer Margin'])

    # 4. Gradient on Total
    if 'Total' in df.columns:
        styled = styled.background_gradient(
            subset=['Total'],
            cmap='Greens',
            vmin=0,
            vmax=df['Total'].max()
        )

    return styled
```

---

### Example 5: Scenario Comparison

```python
def style_scenario_comparison(comparison_df):
    styled = comparison_df.style

    # Format numbers
    styled = styled.format({
        'Base': '£{:,.0f}',
        'Scenario': '£{:,.0f}',
        'Variance': '£{:,.0f}',
        'Var %': '{:.1f}%'
    })

    # Color variance by positive/negative
    def color_variance(row):
        colors = []
        for col in comparison_df.columns:
            if col == 'Variance':
                val = row[col]
                if val > 0:
                    colors.append('background-color: #d4edda; color: #155724')  # Green
                elif val < 0:
                    colors.append('background-color: #f8d7da; color: #721c24')  # Red
                else:
                    colors.append('')
            else:
                colors.append('')
        return colors

    styled = styled.apply(color_variance, axis=1)

    return styled
```

---

## Color Palette Reference

### Success Colors (Green)
- `#d4edda` - Light green (positive variance, success states)
- `#198754` - Dark green (high performance, revenue)
- `#20c997` - Teal (medium performance)

### Warning Colors (Yellow/Orange)
- `#fff3cd` - Light yellow (warnings, pending states)
- `#ffc107` - Amber (moderate thresholds)
- `#fd7e14` - Orange (needs attention)

### Danger Colors (Red)
- `#f8d7da` - Light red (negative variance, errors)
- `#dc3545` - Dark red (losses, critical issues)

### Info Colors (Blue)
- `#e3f2fd` - Light blue (UK region, info states)
- `#0d6efd` - Primary blue (links, actions)

### Neutral Colors
- `#f8f9fa` - Off white (totals, headers)
- `#e9ecef` - Light gray (zebra stripes)
- `#6c757d` - Medium gray (disabled, secondary)

---

## Color Maps for Common Categories

### Country Groups
```python
country_group_colors = {
    'UK': '#e3f2fd',   # Light blue
    'CE': '#fff3e0',   # Light orange
    'EE': '#f3e5f5',   # Light purple
    'ROW': '#e8f5e9'   # Light green
}
```

### Status
```python
status_colors = {
    'Active': '#d4edda',    # Green
    'Pending': '#fff3cd',   # Yellow
    'Inactive': '#f8d7da',  # Red
    'Draft': '#e7f1ff'      # Blue
}
```

### Priority
```python
priority_colors = {
    'High': '#f8d7da',      # Red
    'Medium': '#fff3cd',    # Yellow
    'Low': '#d1ecf1'        # Light blue
}
```

---

## Advanced Techniques

### Technique 1: Combining Multiple Styles

```python
def advanced_styling(df):
    # Start with base styling
    styled = comprehensive_b2b_style(df)

    # Add region coloring
    styled = color_by_category(styled.data, 'Country Group')

    # Add top performers highlight
    styled = highlight_top_n(styled.data, 'Total Revenue', n=5)

    return styled
```

### Technique 2: Conditional Row Highlighting

```python
def highlight_by_condition(df):
    def apply_row_style(row):
        if row['Revenue'] > 1000000 and row['Margin'] > 0.3:
            # High revenue + high margin = gold
            return ['background-color: #ffd700'] * len(row)
        elif row['Revenue'] < 10000:
            # Low revenue = red
            return ['background-color: #f8d7da'] * len(row)
        return [''] * len(row)

    return df.style.apply(apply_row_style, axis=1)
```

### Technique 3: Heatmap Styling

```python
def revenue_heatmap(df):
    # Get only date columns
    date_cols = [c for c in df.columns if c.startswith('202')]

    styled = df.style.background_gradient(
        subset=date_cols,
        cmap='RdYlGn',      # Red-Yellow-Green gradient
        axis=None,          # Apply across entire table
        vmin=df[date_cols].min().min(),
        vmax=df[date_cols].max().max()
    )

    return styled
```

---

## Best Practices

### 1. Don't Over-Style
✅ **Good**: 2-3 styling techniques per table
❌ **Bad**: Every column different color, multiple gradients

### 2. Consistent Color Scheme
- Use the same colors for the same meanings across all views
- Green = positive, Red = negative, Yellow = warning

### 3. Readable Text
- Ensure sufficient contrast between text and background
- Don't use colors that make text unreadable

### 4. Performance
- Styling large dataframes (>1000 rows) can be slow
- Apply styling only to displayed data, not entire dataset
- Use `df.head(100)` for large tables

### 5. Accessibility
- Don't rely solely on color to convey information
- Use bold, icons, or text labels for critical information

---

## Troubleshooting

### Issue: Styling Not Appearing

**Problem**: DataFrame looks normal without styling

**Solutions**:
1. Ensure you're using `st.dataframe(styled_df)` not `st.dataframe(df)`
2. Check that you're returning the styled object
3. Verify pandas Styler is being used: `isinstance(styled_df, pd.io.formats.style.Styler)`

### Issue: Performance Slow

**Problem**: Page takes long to load with styled tables

**Solutions**:
1. Limit rows displayed: `df.head(50)`
2. Simplify styling (fewer operations)
3. Use `st.data_editor()` instead for large editable tables

### Issue: Colors Not Showing

**Problem**: Background colors not appearing

**Solutions**:
1. Use full format: `'background-color: #hexcode'`
2. Check color hex codes are valid
3. Ensure no conflicting CSS in custom markdown

---

## Testing Your Styles

```python
# Create test data
test_df = pd.DataFrame({
    'Customer': ['A', 'B', 'C', 'D', 'E'],
    'Revenue': [1000000, 750000, 500000, 250000, 100000],
    'Margin': [0.3, 0.25, 0.2, 0.15, 0.1],
    'Region': ['UK', 'CE', 'EE', 'ROW', 'UK']
})

# Apply styling
from dataframe_styles import comprehensive_b2b_style
styled = comprehensive_b2b_style(test_df)

# Display
st.dataframe(styled)
```

---

## Resources

### Pandas Styling Documentation
https://pandas.pydata.org/docs/user_guide/style.html

### Color Picker
https://htmlcolorcodes.com/

### ColorBrewer (Data Visualization Colors)
https://colorbrewer2.org/

### Matplotlib Colormaps
- `'Greens'` - Light to dark green
- `'RdYlGn'` - Red-Yellow-Green diverging
- `'Blues'` - Light to dark blue
- `'YlOrRd'` - Yellow-Orange-Red
- `'Viridis'` - Perceptually uniform

---

## Summary

Row and cell formatting transforms static data tables into visual dashboards that highlight patterns and outliers instantly. The Budget Planning App now supports:

✅ Currency formatting
✅ Gradient coloring
✅ Conditional highlighting
✅ Row-level coloring by category
✅ Threshold-based colors
✅ Bold/italic styling
✅ Zebra striping
✅ Custom color maps

Use the `dataframe_styles.py` module for consistent, reusable styling across all views!
