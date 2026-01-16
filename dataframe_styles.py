"""
Reusable dataframe styling functions for Budget Planning App
"""
import pandas as pd
import numpy as np


def style_currency_table(df, currency_cols, gradient_col=None):
    """
    Apply standard currency formatting with optional gradient

    Args:
        df: DataFrame to style
        currency_cols: List of column names to format as currency
        gradient_col: Optional column name to apply green gradient
    """
    styled = df.style

    # Format currency columns
    format_dict = {col: '£{:,.0f}' for col in currency_cols if col in df.columns}
    styled = styled.format(format_dict)

    # Apply gradient if specified
    if gradient_col and gradient_col in df.columns:
        styled = styled.background_gradient(
            subset=[gradient_col],
            cmap='Greens',
            vmin=df[gradient_col].min(),
            vmax=df[gradient_col].max()
        )

    return styled


def highlight_top_n(df, value_col, n=3, color='#ffd700'):
    """
    Highlight the top N rows based on a value column

    Args:
        df: DataFrame to style
        value_col: Column to determine top rows
        n: Number of top rows to highlight
        color: Background color for highlighted rows
    """
    def highlight_rows(row):
        top_n_values = df.nlargest(n, value_col)[value_col].values
        if row[value_col] in top_n_values:
            return [f'background-color: {color}'] * len(row)
        return [''] * len(row)

    return df.style.apply(highlight_rows, axis=1)


def color_by_category(df, category_col, color_map=None):
    """
    Color rows based on category values

    Args:
        df: DataFrame to style
        category_col: Column containing categories
        color_map: Dict mapping category values to colors
    """
    if color_map is None:
        # Default color map for Country Groups
        color_map = {
            'UK': '#e3f2fd',      # Light blue
            'CE': '#fff3e0',      # Light orange
            'EE': '#f3e5f5',      # Light purple
            'ROW': '#e8f5e9'      # Light green
        }

    def apply_colors(row):
        color = color_map.get(row[category_col], '')
        if color:
            return [f'background-color: {color}'] * len(row)
        return [''] * len(row)

    return df.style.apply(apply_colors, axis=1)


def highlight_negative_values(df, cols):
    """
    Highlight negative values in red

    Args:
        df: DataFrame to style
        cols: List of columns to check for negative values
    """
    def highlight_negative(val):
        if pd.notna(val) and isinstance(val, (int, float)) and val < 0:
            return 'color: red; font-weight: bold'
        return ''

    return df.style.applymap(highlight_negative, subset=cols)


def highlight_zero_values(df, cols, color='#f8d7da'):
    """
    Highlight zero or missing values

    Args:
        df: DataFrame to style
        cols: List of columns to check
        color: Background color for zeros
    """
    def highlight_zero(val):
        if pd.isna(val) or val == 0:
            return f'background-color: {color}'
        return ''

    return df.style.applymap(highlight_zero, subset=cols)


def zebra_stripes(df, even_color='#f9f9f9', odd_color='#ffffff'):
    """
    Apply alternating row colors (zebra striping)

    Args:
        df: DataFrame to style
        even_color: Color for even rows
        odd_color: Color for odd rows
    """
    def stripe_rows(row):
        color = even_color if row.name % 2 == 0 else odd_color
        return [f'background-color: {color}'] * len(row)

    return df.style.apply(stripe_rows, axis=1)


def apply_thresholds(df, col, thresholds):
    """
    Apply color based on threshold ranges

    Args:
        df: DataFrame to style
        col: Column to apply thresholds to
        thresholds: List of (value, color) tuples, e.g., [(0, 'red'), (50, 'yellow'), (100, 'green')]
    """
    def color_by_threshold(val):
        if pd.isna(val):
            return ''

        # Sort thresholds by value
        sorted_thresholds = sorted(thresholds, key=lambda x: x[0], reverse=True)

        for threshold_val, color in sorted_thresholds:
            if val >= threshold_val:
                return f'background-color: {color}'

        return ''

    return df.style.applymap(color_by_threshold, subset=[col])


def comprehensive_b2b_style(df):
    """
    Apply comprehensive styling specifically for B2B customer data

    Includes:
    - Currency formatting
    - Gradient on Total column
    - Highlight negative margins
    - Zebra striping
    """
    styled = df.style

    # Identify currency columns
    currency_cols = ['Customer Margin', 'Total'] + [c for c in df.columns if c.startswith('202')]
    currency_cols = [c for c in currency_cols if c in df.columns]

    # Format currency
    format_dict = {col: '£{:,.0f}' for col in currency_cols}
    styled = styled.format(format_dict)

    # Gradient on Total if exists
    if 'Total' in df.columns and not df['Total'].empty:
        styled = styled.background_gradient(
            subset=['Total'],
            cmap='RdYlGn',
            vmin=df['Total'].min(),
            vmax=df['Total'].max()
        )

    # Highlight negative margins
    if 'Customer Margin' in df.columns:
        def highlight_negative_margin(val):
            if pd.notna(val) and val < 0:
                return 'color: red; font-weight: bold'
            return ''
        styled = styled.applymap(highlight_negative_margin, subset=['Customer Margin'])

    # Add borders and alignment
    styled = styled.set_properties(**{
        'border': '1px solid #ddd',
        'text-align': 'right'
    }, subset=currency_cols)

    return styled


def format_percentage_column(df, cols, decimals=1):
    """
    Format columns as percentages

    Args:
        df: DataFrame to style
        cols: List of columns to format
        decimals: Number of decimal places
    """
    format_dict = {col: f'{{:.{decimals}f}}%' for col in cols if col in df.columns}
    return df.style.format(format_dict)


def highlight_changes(df, comparison_df, highlight_color='#ffffcc'):
    """
    Highlight cells that have changed compared to another dataframe

    Args:
        df: Current DataFrame
        comparison_df: DataFrame to compare against
        highlight_color: Color for changed cells
    """
    def highlight_diff(val, ref_val):
        if pd.notna(val) and pd.notna(ref_val) and val != ref_val:
            return f'background-color: {highlight_color}'
        return ''

    # This is more complex and would need to be applied cell by cell
    # Simplified version:
    mask = df != comparison_df
    return df.style.apply(lambda x: [f'background-color: {highlight_color}' if mask.loc[x.name, col] else ''
                                      for col in df.columns], axis=1)


# Example usage combinations
def style_dashboard_customers(df):
    """Pre-configured styling for dashboard top customers"""
    styled = df.style

    # Currency formatting
    styled = styled.format({'Total Revenue': '£{:,.0f}'})

    # Green gradient on revenue
    styled = styled.background_gradient(
        subset=['Total Revenue'],
        cmap='Greens',
        vmin=df['Total Revenue'].min(),
        vmax=df['Total Revenue'].max()
    )

    # Bold top 3
    def bold_top_3(s):
        is_top_3 = [True if i < 3 else False for i in range(len(s))]
        return ['font-weight: bold' if v else '' for v in is_top_3]

    styled = styled.apply(bold_top_3, axis=0)

    return styled


def style_pl_view(df):
    """Pre-configured styling for P&L statement view"""
    styled = df.style

    # Identify total rows (lines containing 'Total' or 'EBITDA')
    def bold_total_rows(row):
        if 'Total' in str(row.name) or 'EBITDA' in str(row.name):
            return ['font-weight: bold; background-color: #f0f0f0'] * len(row)
        return [''] * len(row)

    styled = styled.apply(bold_total_rows, axis=1)

    # Color negative values (costs) in red
    def color_negatives(val):
        if pd.notna(val) and isinstance(val, (int, float)) and val < 0:
            return 'color: #d9534f'
        return ''

    styled = styled.applymap(color_negatives)

    return styled


def style_revenue_inputs(df):
    """
    Pre-configured styling for DTC revenue inputs
    Formats rows based on metric type:
    - Currency: Total Revenue, Marketing Budget
    - Percentage: Conversion Rate
    - Number: Traffic, Customers, Orders
    """
    styled = df.style

    # Define metric categories
    currency_metrics = ['Total Revenue', 'Marketing Budget']
    percentage_metrics = ['Conversion Rate']
    number_metrics = ['Traffic', 'New Customers', 'New Subscription Customers',
                     'Recurring Subscription Customers', 'Returning Customers', 'Total Orders']

    # Format each row based on metric type
    def format_by_metric(row):
        metric_name = str(row.name)
        formats = []

        for col in df.columns:
            val = row[col]

            # Currency formatting
            if any(m in metric_name for m in currency_metrics):
                if pd.notna(val):
                    formats.append(f'£{val:,.0f}')
                else:
                    formats.append('-')

            # Percentage formatting
            elif any(m in metric_name for m in percentage_metrics):
                if pd.notna(val):
                    # Assume value is in decimal form (0.15 = 15%)
                    if val < 1 and val > 0:
                        formats.append(f'{val*100:.1f}%')
                    else:
                        # If already in percentage form
                        formats.append(f'{val:.1f}%')
                else:
                    formats.append('-')

            # Number formatting (with thousand separators)
            else:
                if pd.notna(val):
                    formats.append(f'{val:,.0f}')
                else:
                    formats.append('-')

        return formats

    # Apply row-wise formatting
    for idx in df.index:
        row_format = {}
        metric_name = str(idx)

        for col in df.columns:
            # Currency formatting
            if any(m in metric_name for m in currency_metrics):
                row_format[col] = '£{:,.0f}'

            # Percentage formatting (multiply by 100)
            elif any(m in metric_name for m in percentage_metrics):
                row_format[col] = lambda x: f'{x*100:.1f}%' if pd.notna(x) else '-'

            # Number formatting
            else:
                row_format[col] = '{:,.0f}'

        styled = styled.format(row_format, subset=pd.IndexSlice[idx, :])

    # Add zebra stripes for readability
    def stripe_rows(row):
        if list(df.index).index(row.name) % 2 == 0:
            return ['background-color: #f9f9f9'] * len(row)
        return ['background-color: #ffffff'] * len(row)

    styled = styled.apply(stripe_rows, axis=1)

    # Highlight revenue and budget rows
    def highlight_key_metrics(row):
        metric_name = str(row.name)
        if 'Total Revenue' in metric_name:
            return ['background-color: #d4edda; font-weight: bold'] * len(row)
        elif 'Marketing Budget' in metric_name:
            return ['background-color: #fff3cd; font-weight: bold'] * len(row)
        return [''] * len(row)

    styled = styled.apply(highlight_key_metrics, axis=1)

    # Right-align all numeric columns
    styled = styled.set_properties(**{'text-align': 'right'})

    return styled
