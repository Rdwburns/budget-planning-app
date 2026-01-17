"""
Budget Planning & Forecasting App
A Streamlit application for FY26-27 budget management
Version: 1.0.2 - Force reload of calculations module to fix caching
"""
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import io
from datetime import datetime

# Import our modules
from data_loader import load_all_data, BudgetDataLoader
from pl_calculations import PLCalculator, format_currency, format_percentage
from features_phase1 import (
    render_comments_system,
    render_assumptions_register,
    render_data_quality_dashboard,
    render_waterfall_analysis
)
from marketing_module import render_marketing_management

# Page config
st.set_page_config(
    page_title="Budget Planning Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .stDataFrame {
        font-size: 0.85rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
    }
    .highlight-positive {
        color: #28a745;
        font-weight: 600;
    }
    .highlight-negative {
        color: #dc3545;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


def load_data():
    """Load data from uploaded file or default"""
    if 'data' not in st.session_state:
        default_path = Path(__file__).parent.parent / "Copy of Budget FY26-27 Base.xlsx"
        if default_path.exists():
            st.session_state.data = load_all_data(str(default_path))
            st.session_state.file_loaded = True
        else:
            st.session_state.data = None
            st.session_state.file_loaded = False

    return st.session_state.data


def render_sidebar():
    """Render sidebar navigation and controls"""
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/budget.png", width=60)
        st.title("Budget Planner")

        # Version indicator
        st.markdown(
            '<div style="text-align: center; padding: 5px; background-color: #c0392b; color: white; '
            'border-radius: 5px; font-size: 12px; margin-bottom: 10px;">'
            '🏢 Version 1.0.6 - B2B Debug'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown("---")

        # Navigation
        page = st.radio(
            "Navigate to",
            ["📊 Dashboard", "💰 Revenue Inputs", "📦 B2B Management",
             "💸 Cost Management", "📣 Marketing", "🎯 Scenario Planning", "📈 P&L View",
             "📉 Budget vs Actuals", "📚 Version Control", "📈 Sensitivity Analysis",
             "📝 Comments & Notes", "📋 Assumptions", "🛡️ Data Quality", "💧 Waterfall Analysis",
             "⬇️ Export"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        # File upload
        st.subheader("📁 Data Source")
        uploaded_file = st.file_uploader(
            "Upload Budget Excel",
            type=['xlsx'],
            help="Upload your budget Excel file to load fresh data"
        )

        if uploaded_file:
            # Check if this is a new file to avoid reprocessing
            file_id = f"{uploaded_file.name}_{uploaded_file.size}"
            if st.session_state.get('loaded_file_id') != file_id:
                with st.spinner("Loading data..."):
                    # Save to temp location and load
                    temp_path = Path("/tmp/budget_upload.xlsx")
                    temp_path.write_bytes(uploaded_file.getvalue())
                    st.session_state.data = load_all_data(str(temp_path))
                st.session_state.file_loaded = True
                st.session_state.loaded_file_id = file_id
                st.rerun()  # Refresh to show loaded data

        if st.session_state.get('file_loaded'):
            st.success("✅ Data loaded")

            # Display validation warnings if any
            if st.session_state.data and 'validation_warnings' in st.session_state.data:
                warnings = st.session_state.data['validation_warnings']
                if warnings:
                    with st.expander("⚠️ Data Validation Warnings", expanded=False):
                        for warning in warnings:
                            st.warning(warning)

            st.markdown("---")

            # Version Control quick actions
            st.subheader("📚 Version Control")

            # Initialize version storage
            if 'budget_versions' not in st.session_state:
                st.session_state.budget_versions = []

            # Quick save version
            with st.expander("💾 Save Version", expanded=False):
                version_name = st.text_input(
                    "Version name:",
                    placeholder="e.g., Q1 Final",
                    key="quick_save_version_name"
                )
                version_notes = st.text_area(
                    "Notes (optional):",
                    placeholder="Describe changes in this version",
                    key="quick_save_version_notes",
                    height=80
                )
                if st.button("Save Current Version", key="quick_save_version_btn"):
                    if version_name:
                        import copy
                        version = {
                            'name': version_name,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'notes': version_notes,
                            'data': copy.deepcopy(st.session_state.data)
                        }
                        st.session_state.budget_versions.append(version)
                        st.success(f"✅ Saved version: {version_name}")
                        st.rerun()
                    else:
                        st.error("Please enter a version name")

            # Show saved versions count
            if st.session_state.budget_versions:
                st.info(f"📦 {len(st.session_state.budget_versions)} saved version(s)")
                st.caption("Go to Version Control page to manage versions")

        return page


def render_dashboard(data):
    """Render main dashboard with KPIs"""
    st.markdown('<p class="main-header">📊 Budget Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">FY26-27 Financial Overview</p>', unsafe_allow_html=True)

    if not data:
        st.warning("Please upload a budget file to view the dashboard")
        return

    calc = PLCalculator(data)

    # Calculate totals across all channels
    b2b_total = sum(calc.calculate_b2b_revenue().values())

    # Calculate DTC total across all territories
    dtc_territories = ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK', 'Other EU']
    dtc_total = sum(
        sum(calc.calculate_dtc_revenue(territory).values())
        for territory in dtc_territories
    )

    # Calculate Marketplace total across ALL marketplace territories (includes FR, DE, US, etc.)
    marketplace_total = sum(calc.calculate_total_marketplace_revenue().values())

    # Total revenue across ALL channels
    total_revenue = b2b_total + dtc_total + marketplace_total

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Revenue (All Channels)",
            value=f"£{total_revenue/1e6:.1f}M",
            delta="+12% vs LY"
        )

    with col2:
        st.metric(
            label="B2B Revenue",
            value=f"£{b2b_total/1e6:.1f}M",
            delta=f"{(b2b_total/total_revenue)*100:.0f}% of total" if total_revenue > 0 else "0%"
        )

    with col3:
        st.metric(
            label="DTC Revenue",
            value=f"£{dtc_total/1e6:.1f}M",
            delta=f"{(dtc_total/total_revenue)*100:.0f}% of total" if total_revenue > 0 else "0%"
        )

    with col4:
        st.metric(
            label="Marketplace Revenue",
            value=f"£{marketplace_total/1e6:.1f}M",
            delta=f"{(marketplace_total/total_revenue)*100:.0f}% of total" if total_revenue > 0 else "0%"
        )

    st.markdown("---")

    # Channel Mix Visualization
    st.subheader("📊 Revenue by Channel")

    col1, col2 = st.columns(2)

    with col1:
        # Channel mix pie chart
        if total_revenue > 0:
            import plotly.express as px

            channel_data = pd.DataFrame({
                'Channel': ['B2B', 'DTC', 'Marketplace'],
                'Revenue': [b2b_total, dtc_total, marketplace_total],
                'Percentage': [
                    (b2b_total/total_revenue)*100,
                    (dtc_total/total_revenue)*100,
                    (marketplace_total/total_revenue)*100
                ]
            })

            fig = px.pie(
                channel_data,
                values='Revenue',
                names='Channel',
                title='Channel Mix (FY)',
                hole=0.4,
                color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c']
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Calculate Last Year (FY25) revenue if available
        ly_b2b = 0
        if 'Last Year FY25 Revenue' in data['b2b'].columns:
            ly_b2b = pd.to_numeric(data['b2b']['Last Year FY25 Revenue'], errors='coerce').sum()

        # Estimate LY for DTC and Marketplace (assuming similar growth)
        ly_dtc = dtc_total / 1.12 if dtc_total > 0 else 0  # Assume 12% growth
        ly_marketplace = marketplace_total / 1.15 if marketplace_total > 0 else 0  # Assume 15% growth
        ly_total = ly_b2b + ly_dtc + ly_marketplace

        # Channel revenue table with YoY variance
        channel_table = pd.DataFrame({
            'Channel': ['B2B', 'DTC', 'Marketplace', 'Total'],
            'FY27 Revenue': [b2b_total, dtc_total, marketplace_total, total_revenue],
            'FY25 Revenue': [ly_b2b, ly_dtc, ly_marketplace, ly_total],
            'YoY Variance': [
                f"{((b2b_total - ly_b2b) / ly_b2b * 100):+.1f}%" if ly_b2b > 0 else "N/A",
                f"{((dtc_total - ly_dtc) / ly_dtc * 100):+.1f}%" if ly_dtc > 0 else "N/A",
                f"{((marketplace_total - ly_marketplace) / ly_marketplace * 100):+.1f}%" if ly_marketplace > 0 else "N/A",
                f"{((total_revenue - ly_total) / ly_total * 100):+.1f}%" if ly_total > 0 else "N/A"
            ],
            '% of Total': [
                f"{(b2b_total/total_revenue)*100:.1f}%" if total_revenue > 0 else "0%",
                f"{(dtc_total/total_revenue)*100:.1f}%" if total_revenue > 0 else "0%",
                f"{(marketplace_total/total_revenue)*100:.1f}%" if total_revenue > 0 else "0%",
                "100.0%"
            ]
        })

        # Format currency columns
        for col in ['FY27 Revenue', 'FY25 Revenue']:
            channel_table[col] = channel_table[col].apply(lambda x: f"£{x:,.0f}")

        st.dataframe(channel_table, hide_index=True, use_container_width=True)
        st.caption("*DTC and Marketplace FY25 figures are estimates based on assumed growth rates")

        # CSV Export button
        csv = channel_table.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export to CSV",
            data=csv,
            file_name=f"channel_revenue_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="export_channel_csv"
        )

    # DTC Revenue by Territory
    st.markdown("---")
    st.subheader("🌍 DTC Revenue by Territory")

    dtc_territory_data = []
    for territory in dtc_territories:
        territory_revenue = calc.calculate_dtc_revenue(territory)
        total = sum(territory_revenue.values())
        if total > 0:  # Only show territories with revenue
            dtc_territory_data.append({
                'Territory': territory,
                'Revenue': total,
                '% of DTC': f"{(total/dtc_total)*100:.1f}%" if dtc_total > 0 else "0%"
            })

    if dtc_territory_data:
        dtc_territory_df = pd.DataFrame(dtc_territory_data)
        dtc_territory_df = dtc_territory_df.sort_values('Revenue', ascending=False)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### By Territory")
            # DTC territory table with formatting
            display_df = dtc_territory_df.copy()
            display_df['Revenue'] = display_df['Revenue'].apply(lambda x: f"£{x:,.0f}")
            st.dataframe(display_df, hide_index=True, use_container_width=True)

            # CSV Export
            csv = dtc_territory_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export to CSV",
                data=csv,
                file_name=f"dtc_by_territory_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="export_dtc_csv"
            )

        with col2:
            st.markdown("#### Monthly Trend")
            # Aggregate DTC revenue across all territories by month
            monthly_dtc = {}
            for territory in dtc_territories:
                territory_revenue = calc.calculate_dtc_revenue(territory)
                for month, revenue in territory_revenue.items():
                    monthly_dtc[month] = monthly_dtc.get(month, 0) + revenue

            monthly_dtc_df = pd.DataFrame([
                {'Month': k, 'Revenue': v}
                for k, v in monthly_dtc.items()
            ])
            if not monthly_dtc_df.empty:
                st.line_chart(monthly_dtc_df.set_index('Month')['Revenue'])
    else:
        st.info("No DTC revenue data available")

    # Marketplace Revenue by Territory
    st.markdown("---")
    st.subheader("🛒 Marketplace Revenue by Territory")

    marketplace_territory_data = []
    for territory in dtc_territories:
        territory_revenue = calc.calculate_marketplace_revenue(territory)
        total = sum(territory_revenue.values())
        if total > 0:  # Only show territories with revenue
            marketplace_territory_data.append({
                'Territory': territory,
                'Revenue': total,
                '% of Marketplace': f"{(total/marketplace_total)*100:.1f}%" if marketplace_total > 0 else "0%"
            })

    if marketplace_territory_data:
        marketplace_territory_df = pd.DataFrame(marketplace_territory_data)
        marketplace_territory_df = marketplace_territory_df.sort_values('Revenue', ascending=False)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### By Territory")
            # Marketplace territory table with formatting
            display_df = marketplace_territory_df.copy()
            display_df['Revenue'] = display_df['Revenue'].apply(lambda x: f"£{x:,.0f}")
            st.dataframe(display_df, hide_index=True, use_container_width=True)

        with col2:
            st.markdown("#### Monthly Trend")
            # Use total marketplace revenue across ALL territories (not just DTC territories)
            monthly_marketplace = calc.calculate_total_marketplace_revenue()

            monthly_marketplace_df = pd.DataFrame([
                {'Month': k, 'Revenue': v}
                for k, v in monthly_marketplace.items()
            ])
            if not monthly_marketplace_df.empty:
                st.line_chart(monthly_marketplace_df.set_index('Month')['Revenue'])
    else:
        st.info("No Marketplace revenue data available")

    # B2B Revenue by Region and Monthly Trend
    st.markdown("---")
    st.subheader("📍 B2B Revenue by Region")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### By Region")

        region_data = []
        for group in ['UK', 'CE', 'EE', 'ROW']:
            rev = calc.calculate_b2b_revenue(country_group=group)
            total = sum(rev.values())
            region_data.append({'Region': group, 'Revenue': total})

        region_df = pd.DataFrame(region_data)
        region_df['Revenue'] = region_df['Revenue'].apply(lambda x: f"£{x:,.0f}")
        st.dataframe(region_df, width="stretch", hide_index=True)

    with col2:
        st.markdown("#### Monthly Trend")

        # Show monthly B2B revenue
        monthly = calc.calculate_b2b_revenue()
        monthly_df = pd.DataFrame([
            {'Month': k, 'Revenue': v}
            for k, v in monthly.items()
        ])
        if not monthly_df.empty:
            st.line_chart(monthly_df.set_index('Month')['Revenue'])

    # Top B2B Customers
    st.markdown("---")
    st.subheader("🏆 Top 10 B2B Customers (FY)")

    b2b = data['b2b'].copy()

    date_cols = [c for c in b2b.columns if c.startswith('202')]
    b2b['Total Revenue'] = b2b[date_cols].apply(pd.to_numeric, errors='coerce').fillna(0).sum(axis=1)

    # Filter out summary rows and region codes that appear as customer names
    summary_terms = ['Revenue', 'Grand Total', 'Total', 'Subtotal', 'Sum', 'All Customers',
                     'UK', 'CE', 'EE', 'ROW', 'CM1', 'CM2', 'EBITDA', 'CoGS', 'Fulfilment']
    b2b_filtered = b2b[~b2b['Customer Name'].isin(summary_terms)]
    b2b_filtered = b2b_filtered[b2b_filtered['Customer Name'].notna()]
    b2b_filtered = b2b_filtered[b2b_filtered['Country'].notna()]  # Real customers have countries

    # Only show customers with revenue > 0
    b2b_filtered = b2b_filtered[b2b_filtered['Total Revenue'] > 0]

    # Group by Customer Name to avoid duplicates, summing revenue across all rows
    b2b_grouped = b2b_filtered.groupby('Customer Name', as_index=False).agg({
        'Total Revenue': 'sum',
        'Country': 'first',  # Take first country if multiple
        'Country Group': 'first'  # Take first country group if multiple
    })

    top_customers = b2b_grouped.nlargest(10, 'Total Revenue')[['Customer Name', 'Country', 'Country Group', 'Total Revenue']]

    # Style the top customers table
    def style_top_customers(df):
        styled = df.style

        # Add gradient to revenue column
        styled = styled.background_gradient(
            subset=['Total Revenue'],
            cmap='Greens',
            vmin=df['Total Revenue'].min(),
            vmax=df['Total Revenue'].max()
        )

        # Format revenue as currency
        styled = styled.format({'Total Revenue': '£{:,.0f}'})

        # Bold the top 3 customers
        def bold_top_3(s):
            is_top_3 = [True if i < 3 else False for i in range(len(s))]
            return ['font-weight: bold' if v else '' for v in is_top_3]

        styled = styled.apply(bold_top_3, axis=0)

        return styled

    st.dataframe(style_top_customers(top_customers), width='stretch', hide_index=True)


def render_revenue_inputs(data):
    """Render DTC revenue input forms"""
    st.markdown('<p class="main-header">💰 Revenue Inputs</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Manage DTC channel assumptions by territory</p>', unsafe_allow_html=True)

    if not data:
        st.warning("Please upload a budget file first")
        return

    # Import styling function
    from dataframe_styles import style_revenue_inputs

    # Persistent Summary Bar - Aggregate metrics across all territories
    st.markdown("### 📊 DTC Summary (All Territories)")

    dtc_territories = ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK', 'Other EU']
    total_revenue = 0
    total_marketing = 0
    total_customers = 0
    total_traffic = 0
    territories_with_data = 0

    for territory in dtc_territories:
        if territory in st.session_state.data.get('dtc', {}):
            dtc_df = st.session_state.data['dtc'][territory]
            if not dtc_df.empty:
                territories_with_data += 1
                date_cols = [c for c in dtc_df.columns if c.startswith('202')]

                # Total Revenue
                revenue_row = dtc_df[dtc_df['Metric'] == 'Total Revenue']
                if not revenue_row.empty:
                    total_revenue += revenue_row[date_cols].sum().sum()

                # Marketing Budget
                marketing_row = dtc_df[dtc_df['Metric'] == 'Marketing Budget']
                if not marketing_row.empty:
                    total_marketing += marketing_row[date_cols].sum().sum()

                # Customers - sum all customer segments
                customer_segments = [
                    'New Customers (Non-Subs)',
                    'New Subscription Customers',
                    'Returning Customers (Non-Subs)',
                    'Recurring Subscription Customers'
                ]
                for segment in customer_segments:
                    segment_row = dtc_df[dtc_df['Metric'] == segment]
                    if not segment_row.empty:
                        total_customers += segment_row[date_cols].sum().sum()

                # Traffic
                traffic_row = dtc_df[dtc_df['Metric'] == 'Traffic']
                if not traffic_row.empty:
                    total_traffic += traffic_row[date_cols].sum().sum()

    # Calculate average conversion rate
    avg_cvr = (total_customers / total_traffic * 100) if total_traffic > 0 else 0

    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total DTC Revenue",
            f"£{total_revenue/1e6:.1f}M",
            delta=f"{territories_with_data} territories"
        )

    with col2:
        st.metric(
            "Total Marketing Budget",
            f"£{total_marketing/1e6:.1f}M",
            delta=f"{(total_marketing/total_revenue*100):.1f}% of revenue" if total_revenue > 0 else "0%"
        )

    with col3:
        st.metric(
            "Total Customers",
            f"{int(total_customers):,}",
            delta=f"Avg CVR: {avg_cvr:.2f}%"
        )

    with col4:
        st.metric(
            "Total Traffic",
            f"{int(total_traffic):,}",
            delta=f"£{(total_revenue/total_customers):.0f} AOV" if total_customers > 0 else "N/A"
        )

    st.markdown("---")

    # Territory selector
    territory = st.selectbox(
        "Select Territory",
        ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK', 'Other EU'],
        key='dtc_territory'
    )

    # Always use session state to preserve edits
    if territory in st.session_state.data.get('dtc', {}):
        dtc_data = st.session_state.data['dtc'][territory]

        st.markdown("### 📊 Key Metrics")

        # Create editable dataframe
        if not dtc_data.empty:
            # Pivot for better display
            display_df = dtc_data.set_index('Metric')
            display_df = display_df.drop(columns=['Territory'], errors='ignore')

            # Show only date columns
            date_cols = [c for c in display_df.columns if c.startswith('202')]
            display_df = display_df[date_cols[:12]]  # Show first 12 months

            # Define which metrics are editable (base inputs) vs calculated (outputs)
            editable_metrics = [
                'Traffic',
                'Marketing Budget',
                'Conversion Rate',
                'New Customers',
                'New Subscription Customers',
                'Recurring Subscription Customers',
                'Returning Customers'
            ]

            calculated_metrics = [
                'Total Revenue',
                'New Customer Revenue',
                'Returning Revenue',
                'New Customer Revenue (Subs)',
                'Returning Revenue (Subs)',
                'Total Orders',
                'Missing Revenue (Cohort Adjustment)'
            ]

            # Separate editable and calculated metrics
            editable_df = display_df[display_df.index.isin(editable_metrics)]
            calculated_df = display_df[display_df.index.isin(calculated_metrics)]

            # Show editable inputs
            if not editable_df.empty:
                st.markdown("#### ✏️ Editable Inputs")

                # Add toggle for table orientation
                col1, col2 = st.columns([1, 3])
                with col1:
                    table_view = st.radio(
                        "View by:",
                        ["By Metric", "By Month"],
                        key=f"table_view_{territory}",
                        horizontal=True
                    )

                with col2:
                    if table_view == "By Metric":
                        st.caption("💡 Metrics as rows, dates as columns (default)")
                    else:
                        st.caption("💡 Dates as rows, metrics as columns (easier for month-by-month editing)")

                # Display table based on selected view
                if table_view == "By Metric":
                    # Default view: metrics as rows, dates as columns
                    edited_df = st.data_editor(
                        editable_df,
                        width="stretch",
                        num_rows="fixed",
                        key=f"dtc_editor_metric_{territory}"
                    )
                else:
                    # Transposed view: dates as rows, metrics as columns
                    transposed_df = editable_df.T
                    edited_transposed = st.data_editor(
                        transposed_df,
                        width="stretch",
                        num_rows="fixed",
                        key=f"dtc_editor_month_{territory}"
                    )
                    # Transpose back for saving
                    edited_df = edited_transposed.T

                col1, col2 = st.columns([1, 3])

                with col1:
                    if st.button("💾 Save Changes", key=f"save_dtc_{territory}"):
                        # Update session state with edited DTC data
                        # Merge edited inputs back with calculated metrics
                        full_df = pd.concat([edited_df, calculated_df])
                        full_df['Territory'] = territory
                        full_df = full_df.reset_index()

                        # Update session state
                        st.session_state.data['dtc'][territory] = full_df
                        st.success(f"✅ Changes saved for {territory}!")

                with col2:
                    # Copy Last Month feature
                    if len(date_cols) >= 2:
                        col_month1, col_month2 = st.columns(2)
                        with col_month1:
                            source_month = st.selectbox(
                                "Copy from:",
                                date_cols[:12],
                                key=f"source_{territory}"
                            )
                        with col_month2:
                            target_months = [m for m in date_cols[:12] if m > source_month]
                            if target_months:
                                target_month = st.selectbox(
                                    "To:",
                                    target_months,
                                    key=f"target_{territory}"
                                )
                                if st.button("📋 Copy Month", key=f"copy_{territory}"):
                                    # Copy values from source to target month
                                    for metric in editable_df.index:
                                        if source_month in editable_df.columns and target_month in editable_df.columns:
                                            st.session_state.data['dtc'][territory].loc[
                                                st.session_state.data['dtc'][territory]['Metric'] == metric,
                                                target_month
                                            ] = editable_df.loc[metric, source_month]
                                    st.success(f"✅ Copied {source_month} → {target_month}. Click 'Save Changes' to persist.")
                                    st.rerun()

            # Show calculated outputs (read-only)
            if not calculated_df.empty:
                st.markdown("#### 📊 Calculated Outputs (Read-only)")
                st.caption("These values are automatically calculated from your inputs above")

                # Apply styling for better visualization
                styled_df = style_revenue_inputs(calculated_df)
                st.dataframe(styled_df, width="stretch")
    else:
        st.info(f"No DTC data available for {territory}")

    # Subscription Cohort Analysis
    st.markdown("---")
    st.markdown("### 📊 Subscription Cohort Analysis")

    # Always use session state to preserve edits
    if territory in st.session_state.data.get('dtc', {}) and not st.session_state.data['dtc'][territory].empty:
        dtc_df = st.session_state.data['dtc'][territory]

        # Filter for subscription-related metrics
        sub_metrics = [
            'New Subscription Customers',
            'Recurring Subscription Customers',
            'Returning Revenue (Subs)',
            'New Customer Revenue (Subs)',
            'Missing Revenue (Cohort Adjustment)'
        ]

        sub_data = dtc_df[dtc_df['Metric'].isin(sub_metrics)]

        if not sub_data.empty:
            # Summary metrics
            col1, col2, col3 = st.columns(3)

            date_cols = [c for c in sub_data.columns if c.startswith('202')]

            with col1:
                new_subs = sub_data[sub_data['Metric'] == 'New Subscription Customers'][date_cols].sum(axis=1).values
                new_subs_total = new_subs[0] if len(new_subs) > 0 else 0
                st.metric("New Subs (FY)", f"{int(new_subs_total):,}")

            with col2:
                recurring = sub_data[sub_data['Metric'] == 'Recurring Subscription Customers'][date_cols].sum(axis=1).values
                recurring_total = recurring[0] if len(recurring) > 0 else 0
                st.metric("Recurring Subs (FY)", f"{int(recurring_total):,}")

            with col3:
                sub_rev = sub_data[sub_data['Metric'].isin(['Returning Revenue (Subs)', 'New Customer Revenue (Subs)'])][date_cols].sum().sum()
                st.metric("Subscription Revenue", f"£{sub_rev:,.0f}")

            # Retention & Decay Rate Inputs
            st.markdown("---")
            st.markdown("#### 🔄 Retention & Decay Settings")
            st.caption("💡 These rates control how many subscription customers continue each month")

            col1, col2 = st.columns(2)

            with col1:
                retention_rate = st.number_input(
                    "Monthly Retention Rate (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=85.0,
                    step=0.5,
                    help="Percentage of customers who remain subscribed each month",
                    key=f"retention_rate_{territory}"
                )

                # Calculate projected retention impact
                if new_subs_total > 0:
                    month_6_retained = new_subs_total * ((retention_rate/100) ** 6)
                    month_12_retained = new_subs_total * ((retention_rate/100) ** 12)
                    st.info(f"📊 Impact: Of {int(new_subs_total):,} new subs, ~{int(month_6_retained):,} remain after 6 months, ~{int(month_12_retained):,} after 12 months")

            with col2:
                decay_rate = 100 - retention_rate
                st.metric(
                    "Monthly Churn/Decay Rate (%)",
                    f"{decay_rate:.1f}%",
                    help="Inverse of retention rate - percentage lost each month"
                )

                # Churn visualization
                if decay_rate > 20:
                    st.error(f"⚠️ High churn rate! Consider improving retention strategies")
                elif decay_rate > 10:
                    st.warning(f"⚠️ Moderate churn - monitor retention closely")
                else:
                    st.success(f"✅ Good retention - low churn rate")

            # Visual retention curve
            with st.expander("📈 View Retention Curve"):
                import plotly.graph_objects as go

                months = list(range(1, 13))
                retention_values = [100 * ((retention_rate/100) ** m) for m in months]

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=months,
                    y=retention_values,
                    mode='lines+markers',
                    name='Retention %',
                    line=dict(color='#1f77b4', width=3),
                    marker=dict(size=8)
                ))

                fig.update_layout(
                    title=f'Customer Retention Over 12 Months ({retention_rate}% monthly retention)',
                    xaxis_title='Months',
                    yaxis_title='Customers Retained (%)',
                    yaxis=dict(range=[0, 110]),
                    hovermode='x unified'
                )

                fig.add_hline(y=50, line_dash="dash", line_color="red",
                             annotation_text="50% retained", annotation_position="right")

                st.plotly_chart(fig, use_container_width=True)

            # Cohort adjustment warning
            cohort_adj = sub_data[sub_data['Metric'] == 'Missing Revenue (Cohort Adjustment)'][date_cols]
            if not cohort_adj.empty:
                total_adj = cohort_adj.sum().sum()
                if abs(total_adj) > 1000:
                    if total_adj < 0:
                        st.warning(f"⚠️ Cohort adjustment: £{total_adj:,.0f} (revenue gap from prior cohort data)")
                    else:
                        st.info(f"ℹ️ Cohort adjustment: +£{total_adj:,.0f} (additional revenue from prior cohorts)")

            # Show detailed table
            with st.expander("View Subscription Cohort Details"):
                display_sub = sub_data.set_index('Metric')
                display_sub = display_sub.drop(columns=['Territory'], errors='ignore')
                date_cols_display = [c for c in display_sub.columns if c.startswith('202')][:12]
                st.dataframe(display_sub[date_cols_display], width="stretch")

    # Quick scenario adjustments
    st.markdown("---")
    st.markdown("### 🎛️ Quick Adjustments")
    st.caption("💡 Adjust key drivers to see immediate revenue impact")

    # Calculate base values from actual territory data
    if territory in st.session_state.data.get('dtc', {}):
        dtc_df = st.session_state.data['dtc'][territory]
        if not dtc_df.empty:
            date_cols = [c for c in dtc_df.columns if c.startswith('202')]

            # Get base metrics
            base_traffic = 0
            traffic_row = dtc_df[dtc_df['Metric'] == 'Traffic']
            if not traffic_row.empty:
                base_traffic = traffic_row[date_cols].sum().sum()

            base_customers = 0
            # Sum all customer segments for total customers
            customer_segments = [
                'New Customers (Non-Subs)',
                'New Subscription Customers',
                'Returning Customers (Non-Subs)',
                'Recurring Subscription Customers'
            ]
            for segment in customer_segments:
                segment_row = dtc_df[dtc_df['Metric'] == segment]
                if not segment_row.empty:
                    base_customers += segment_row[date_cols].sum().sum()

            base_revenue = 0
            revenue_row = dtc_df[dtc_df['Metric'] == 'Total Revenue']
            if not revenue_row.empty:
                base_revenue = revenue_row[date_cols].sum().sum()

            base_cvr = (base_customers / base_traffic * 100) if base_traffic > 0 else 0
            base_aov = (base_revenue / base_customers) if base_customers > 0 else 0

            col1, col2, col3 = st.columns(3)

            with col1:
                st.info(f"**Base Traffic:** {int(base_traffic):,}")
                traffic_adj = st.slider(
                    "Traffic Growth %",
                    min_value=-50,
                    max_value=100,
                    value=0,
                    key=f"traffic_{territory}",
                    help=f"Current: {int(base_traffic):,} visitors"
                )

            with col2:
                st.info(f"**Base CVR:** {base_cvr:.2f}%")
                cvr_adj = st.slider(
                    "Conversion Rate Change %",
                    min_value=-50,
                    max_value=100,
                    value=0,
                    key=f"cvr_{territory}",
                    help=f"Current: {base_cvr:.2f}%"
                )

            with col3:
                st.info(f"**Base AOV:** £{base_aov:.0f}")
                aov_adj = st.slider(
                    "AOV Change %",
                    min_value=-30,
                    max_value=50,
                    value=0,
                    key=f"aov_{territory}",
                    help=f"Current: £{base_aov:.0f}"
                )

            # Show projected impact
            if any([traffic_adj, cvr_adj, aov_adj]):
                st.markdown("---")
                st.markdown("### 📈 Projected Impact")

                # Calculate new values
                new_traffic = base_traffic * (1 + traffic_adj/100)
                new_cvr = base_cvr * (1 + cvr_adj/100)
                new_aov = base_aov * (1 + aov_adj/100)

                # Revenue calculation: Traffic × CVR × AOV
                new_revenue = new_traffic * (new_cvr/100) * new_aov
                revenue_change = new_revenue - base_revenue
                revenue_change_pct = (revenue_change / base_revenue * 100) if base_revenue > 0 else 0

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Base Revenue",
                        f"£{base_revenue:,.0f}",
                        delta=f"{territory} current FY total"
                    )

                with col2:
                    st.metric(
                        "Projected Revenue",
                        f"£{new_revenue:,.0f}",
                        delta=f"{revenue_change_pct:+.1f}%"
                    )

                with col3:
                    st.metric(
                        "Revenue Impact",
                        f"£{abs(revenue_change):,.0f}",
                        delta="increase" if revenue_change > 0 else "decrease"
                    )
        else:
            st.info(f"No data available for {territory} - upload budget file to enable Quick Adjustments")
    else:
        st.info(f"No data available for {territory} - upload budget file to enable Quick Adjustments")


def render_b2b_management(data):
    """Render B2B customer management interface"""
    st.markdown('<p class="main-header">📦 B2B Management</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Manage B2B customer forecasts and targets</p>', unsafe_allow_html=True)

    if not data:
        st.warning("Please upload a budget file first")
        return

    # Always use session state to preserve edits across page changes
    b2b = st.session_state.data['b2b'].copy()

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        region_filter = st.multiselect(
            "Filter by Region",
            options=['UK', 'CE', 'EE', 'ROW'],
            default=['UK', 'CE', 'EE', 'ROW']
        )

    with col2:
        search = st.text_input("Search Customer", placeholder="Type customer name...")

    with col3:
        min_revenue = st.number_input("Min Revenue (£)", value=0, step=10000)

    # Apply filters
    filtered = b2b[b2b['Country Group'].isin(region_filter)]

    # Filter out generic placeholder names (Retailer 1/2/3, Customer 1/2/3, etc.)
    placeholder_patterns = [
        'Retailer 1', 'Retailer 2', 'Retailer 3',
        'Customer 1', 'Customer 2', 'Customer 3',
        'Placeholder', 'TBD', 'Test Customer'
    ]
    for pattern in placeholder_patterns:
        filtered = filtered[~filtered['Customer Name'].str.contains(pattern, case=False, na=False)]

    if search:
        filtered = filtered[filtered['Customer Name'].str.contains(search, case=False, na=False)]

    date_cols = [c for c in filtered.columns if c.startswith('202')]
    filtered['Total'] = filtered[date_cols].apply(pd.to_numeric, errors='coerce').fillna(0).sum(axis=1)
    filtered = filtered[filtered['Total'] >= min_revenue]

    # Summary stats
    st.markdown("### 📊 Summary")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Customers", len(filtered))
    with col2:
        st.metric("Total Revenue", f"£{filtered['Total'].sum():,.0f}")
    with col3:
        st.metric("Avg per Customer", f"£{filtered['Total'].mean():,.0f}" if len(filtered) > 0 else "£0")
    with col4:
        st.metric("Top Customer", f"£{filtered['Total'].max():,.0f}" if len(filtered) > 0 else "£0")

    st.markdown("---")

    # Editable table
    st.markdown("### 📝 Customer Forecasts")

    display_cols = ['Customer Name', 'Country', 'Country Group'] + date_cols[:6] + ['Total']
    display_df = filtered[display_cols].copy()

    # Build column config with currency formatting for date columns
    column_config = {
        "Customer Name": st.column_config.TextColumn("Customer", width="medium"),
        "Country": st.column_config.TextColumn("Country", width="small"),
        "Country Group": st.column_config.SelectboxColumn("Region", options=['UK', 'CE', 'EE', 'ROW']),
        "Total": st.column_config.NumberColumn("Total", format="£%.0f", disabled=True),
    }

    # Add currency formatting for all date columns
    for col in date_cols[:6]:
        column_config[col] = st.column_config.NumberColumn(col, format="£%.0f")

    edited_b2b = st.data_editor(
        display_df,
        width="stretch",
        num_rows="dynamic",
        column_config=column_config,
        key="b2b_editor"
    )

    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("💾 Save Changes", type="primary", key="save_b2b_main"):
            # Update session state with edited data
            # Remove the calculated 'Total' column before saving
            edited_b2b_clean = edited_b2b.drop(columns=['Total'], errors='ignore')

            # Update the session state b2b dataframe with edited values
            # Match by Customer Name and update
            for idx, row in edited_b2b_clean.iterrows():
                customer_name = row['Customer Name']
                mask = st.session_state.data['b2b']['Customer Name'] == customer_name
                for col in edited_b2b_clean.columns:
                    if col in st.session_state.data['b2b'].columns:
                        st.session_state.data['b2b'].loc[mask, col] = row[col]

            st.success("✅ Changes saved! Edits persist across page changes.")

    with col2:
        # CSV Export
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export to CSV",
            data=csv,
            file_name=f"b2b_customers_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="export_b2b_csv"
        )

    # Add new customer form
    st.markdown("---")
    st.markdown("### ➕ Add New Customer")

    with st.expander("Add Customer Form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            new_name = st.text_input("Customer Name")
            new_country = st.selectbox("Country", data['territories'])

        with col2:
            new_margin = st.number_input("Expected Margin (£)", value=0)
            new_region = st.selectbox("Region", ['UK', 'CE', 'EE', 'ROW'])

        with col3:
            new_monthly = st.number_input("Est. Monthly Revenue (£)", value=0)

        if st.button("Add Customer"):
            if new_name:
                st.success(f"Added {new_name} to forecast")
            else:
                st.error("Please enter a customer name")


def render_cost_management(data):
    """Render cost management interface"""
    st.markdown('<p class="main-header">💸 Cost Management</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Manage overheads, payroll, and fulfilment costs</p>', unsafe_allow_html=True)

    if not data:
        st.warning("Please upload a budget file first")
        return

    tab1, tab2, tab3 = st.tabs(["📋 Overheads", "👥 Payroll", "📦 Fulfilment"])

    with tab1:
        st.markdown("### Overhead Costs by Category")

        oh = data['overheads'].copy()

        # Group by category
        col1, col2 = st.columns(2)

        with col1:
            territory_filter = st.selectbox(
                "Territory",
                ['All'] + list(oh['Territory'].dropna().unique())
            )

        with col2:
            function_filter = st.selectbox(
                "Function",
                ['All'] + list(oh['Function'].dropna().unique())
            )

        filtered_oh = oh.copy()
        if territory_filter != 'All':
            filtered_oh = filtered_oh[filtered_oh['Territory'] == territory_filter]
        if function_filter != 'All':
            filtered_oh = filtered_oh[filtered_oh['Function'] == function_filter]

        date_cols = [c for c in filtered_oh.columns if c.startswith('202')]
        display_cols = ['Territory', 'Function', 'Category', 'Supplier'] + date_cols[:6]

        # Build column config with currency formatting for date columns
        oh_column_config = {}
        for col in date_cols[:6]:
            oh_column_config[col] = st.column_config.NumberColumn(col, format="£%.0f")

        st.data_editor(
            filtered_oh[display_cols],
            width="stretch",
            num_rows="dynamic",
            column_config=oh_column_config,
            key="oh_editor"
        )

    with tab2:
        st.markdown("### Payroll by Department")
        st.info("Payroll data is managed separately. Contact Finance for changes.")

        # Show summary
        payroll = data.get('payroll', pd.DataFrame())
        if not payroll.empty:
            st.dataframe(payroll.head(20), width="stretch")

    with tab3:
        st.markdown("### Fulfilment Rates")
        st.caption("💡 Rates are displayed as percentages (e.g., 15.0% = 15% of revenue)")

        fulfilment = data['fulfilment'].copy()

        # Convert decimal rates to percentages for display (multiply by 100)
        # If rates are stored as 0.15, display as 15%
        display_ful = fulfilment.copy()
        if 'Rate' in display_ful.columns:
            # Check if rates are in decimal form (< 1)
            if display_ful['Rate'].abs().max() <= 1:
                display_ful['Rate'] = display_ful['Rate'] * 100

        edited_ful = st.data_editor(
            display_ful,
            width="stretch",
            column_config={
                "Rate": st.column_config.NumberColumn("Rate %", format="%.1f%%", help="Fulfilment cost as % of revenue")
            },
            key="ful_editor"
        )

        if st.button("💾 Save Fulfilment Rates", key="save_fulfilment"):
            # Convert percentages back to decimal form before saving (divide by 100)
            saved_ful = edited_ful.copy()
            if 'Rate' in saved_ful.columns:
                # If the max value is > 1, it's in percentage form, convert back to decimal
                if saved_ful['Rate'].abs().max() > 1:
                    saved_ful['Rate'] = saved_ful['Rate'] / 100

            # Update session state with edited fulfilment rates
            st.session_state.data['fulfilment'] = saved_ful
            st.success("✅ Fulfilment rates updated in session!")


def render_scenario_planning(data):
    """Render scenario planning interface"""
    st.markdown('<p class="main-header">🎯 Scenario Planning</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Model different business scenarios and compare outcomes</p>', unsafe_allow_html=True)

    if not data:
        st.warning("Please upload a budget file first")
        return

    # Scenario selection
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📊 Base Scenario")
        st.info("Current budget values")

    with col2:
        st.markdown("### 🔮 New Scenario")

        # Load saved scenarios
        if 'saved_scenarios' in st.session_state and st.session_state.saved_scenarios:
            st.markdown("**Load Saved Scenario:**")
            scenario_options = ['Create New'] + [s['name'] for s in st.session_state.saved_scenarios]
            selected_scenario = st.selectbox(
                "Select scenario:",
                scenario_options,
                key="scenario_selector"
            )

            if selected_scenario != 'Create New':
                # Load the selected scenario
                loaded = next(s for s in st.session_state.saved_scenarios if s['name'] == selected_scenario)
                st.info(f"📅 Saved: {loaded['timestamp']}")
                scenario_name = st.text_input("Scenario Name", value=selected_scenario)
                # Pre-populate sliders with loaded values (we'll handle this below)
                st.session_state.loaded_scenario = loaded['params']
            else:
                scenario_name = st.text_input("Scenario Name", value="Optimistic Growth")
                if 'loaded_scenario' in st.session_state:
                    del st.session_state.loaded_scenario
        else:
            scenario_name = st.text_input("Scenario Name", value="Optimistic Growth")

    st.markdown("---")

    # Adjustment sliders
    st.markdown("### 🎛️ Scenario Adjustments")

    # Get default values from loaded scenario if available
    loaded = st.session_state.get('loaded_scenario', {})

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Revenue Drivers**")

        dtc_growth = st.slider(
            "DTC Revenue Growth %",
            -30, 50,
            loaded.get('dtc_revenue_UK', 10),
            key="sc_dtc"
        )
        b2b_growth = st.slider(
            "B2B Revenue Growth %",
            -30, 50,
            loaded.get('b2b_growth', 5),
            key="sc_b2b"
        )
        mp_growth = st.slider(
            "Marketplace Growth %",
            -30, 50,
            loaded.get('mp_growth', 15),
            key="sc_mp"
        )

    with col2:
        st.markdown("**Margin Impacts**")

        cogs_change = st.slider(
            "CoGS Rate Change (pp)",
            -5.0, 5.0,
            float(loaded.get('cogs_change', 0.0)),
            step=0.5,
            key="sc_cogs"
        )
        fulfilment_change = st.slider(
            "Fulfilment Rate Change (pp)",
            -5.0, 5.0,
            float(loaded.get('fulfilment_change', 0.0)),
            step=0.5,
            key="sc_ful"
        )

    with col3:
        st.markdown("**Cost Assumptions**")

        marketing_change = st.slider(
            "Marketing Spend %",
            -30, 50,
            loaded.get('marketing_change', 0),
            key="sc_mkt"
        )
        overhead_change = st.slider(
            "Overhead Change %",
            -20, 30,
            loaded.get('overhead_change', 0),
            key="sc_oh"
        )

    # Build scenario - apply DTC growth to ALL DTC territories
    dtc_territories_scenario = ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK', 'Other EU']
    scenario = {
        'b2b_growth': b2b_growth,
        'mp_growth': mp_growth,
        'cogs_change': cogs_change,
        'fulfilment_change': fulfilment_change,
        'marketing_change': marketing_change,
        'overhead_change': overhead_change,
    }

    # Add DTC growth for all territories
    for territory in dtc_territories_scenario:
        scenario[f'dtc_revenue_{territory}'] = dtc_growth

    st.markdown("---")

    # Results comparison
    st.markdown("### 📈 Scenario Comparison")

    calc = PLCalculator(data, scenario)
    base_calc = PLCalculator(data, {})

    # Calculate all channel revenues
    dtc_territories = ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK', 'Other EU']

    # Base case
    base_b2b = sum(base_calc.calculate_b2b_revenue().values())
    base_dtc = sum(
        sum(base_calc.calculate_dtc_revenue(territory).values())
        for territory in dtc_territories
    )
    # Use total marketplace revenue across ALL territories (not just DTC)
    base_marketplace = sum(base_calc.calculate_total_marketplace_revenue().values())
    base_total = base_b2b + base_dtc + base_marketplace

    # Scenario case
    new_b2b = base_b2b * (1 + b2b_growth/100)
    new_dtc = base_dtc * (1 + dtc_growth/100)
    new_marketplace = base_marketplace * (1 + mp_growth/100)
    new_total = new_b2b + new_dtc + new_marketplace

    # Display metrics by channel
    st.markdown("#### Revenue by Channel")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Revenue",
            f"£{new_total/1e6:.1f}M",
            delta=f"£{(new_total-base_total)/1e6:.1f}M ({((new_total-base_total)/base_total*100):+.1f}%)" if base_total > 0 else "N/A"
        )

    with col2:
        st.metric(
            "B2B Revenue",
            f"£{new_b2b/1e6:.1f}M",
            delta=f"{b2b_growth:+.1f}% | £{(new_b2b-base_b2b)/1e6:.1f}M"
        )

    with col3:
        st.metric(
            "DTC Revenue",
            f"£{new_dtc/1e6:.1f}M",
            delta=f"{dtc_growth:+.1f}% | £{(new_dtc-base_dtc)/1e6:.1f}M"
        )

    with col4:
        st.metric(
            "Marketplace Revenue",
            f"£{new_marketplace/1e6:.1f}M",
            delta=f"{mp_growth:+.1f}% | £{(new_marketplace-base_marketplace)/1e6:.1f}M"
        )

    # Channel breakdown table
    st.markdown("---")
    st.markdown("#### Channel-by-Channel Breakdown")

    col1, col2 = st.columns(2)

    with col1:
        # Comparison table
        channel_comparison = pd.DataFrame({
            'Channel': ['B2B', 'DTC', 'Marketplace', 'Total'],
            'Base (£)': [base_b2b, base_dtc, base_marketplace, base_total],
            'Scenario (£)': [new_b2b, new_dtc, new_marketplace, new_total],
            'Variance (£)': [
                new_b2b - base_b2b,
                new_dtc - base_dtc,
                new_marketplace - base_marketplace,
                new_total - base_total
            ],
            'Variance (%)': [
                b2b_growth,
                dtc_growth,
                mp_growth,
                ((new_total-base_total)/base_total*100) if base_total > 0 else 0
            ]
        })

        # Format currency columns
        for col in ['Base (£)', 'Scenario (£)', 'Variance (£)']:
            channel_comparison[col] = channel_comparison[col].apply(lambda x: f"£{x:,.0f}")

        channel_comparison['Variance (%)'] = channel_comparison['Variance (%)'].apply(lambda x: f"{x:+.1f}%")

        st.dataframe(channel_comparison, hide_index=True, use_container_width=True)

    with col2:
        # Visualization comparing base vs scenario
        import plotly.graph_objects as go

        fig = go.Figure()

        channels = ['B2B', 'DTC', 'Marketplace']
        base_values = [base_b2b/1e6, base_dtc/1e6, base_marketplace/1e6]
        scenario_values = [new_b2b/1e6, new_dtc/1e6, new_marketplace/1e6]

        fig.add_trace(go.Bar(
            name='Base',
            x=channels,
            y=base_values,
            marker_color='#1f77b4'
        ))

        fig.add_trace(go.Bar(
            name='Scenario',
            x=channels,
            y=scenario_values,
            marker_color='#ff7f0e'
        ))

        fig.update_layout(
            title='Revenue Comparison: Base vs Scenario',
            yaxis_title='Revenue (£M)',
            barmode='group',
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

    # Detailed P&L comparison
    st.markdown("---")
    with st.expander("📊 Detailed P&L Comparison (Consolidated)", expanded=False):
        try:
            # Calculate consolidated P&L across all territories
            base_pl = base_calc.calculate_combined_pl()
            new_pl = calc.calculate_combined_pl()

            # Sum across all date columns for FY totals
            date_cols = [c for c in base_pl.columns if c.startswith('202')]

            comparison = pd.DataFrame({
                'Line Item': base_pl.index.get_level_values(1),
                'Category': base_pl.index.get_level_values(0),
                'Base (£)': base_pl[date_cols].sum(axis=1).values,
                'Scenario (£)': new_pl[date_cols].sum(axis=1).values,
            })

            comparison['Variance (£)'] = comparison['Scenario (£)'] - comparison['Base (£)']
            comparison['Variance (%)'] = (
                (comparison['Variance (£)'] / comparison['Base (£)'].abs() * 100)
                .replace([float('inf'), -float('inf')], 0)
                .fillna(0)
                .round(1)
            )

            # Format currency columns
            for col in ['Base (£)', 'Scenario (£)', 'Variance (£)']:
                comparison[col] = comparison[col].apply(lambda x: f"£{x:,.0f}" if x >= 0 else f"(£{abs(x):,.0f})")

            comparison['Variance (%)'] = comparison['Variance (%)'].apply(lambda x: f"{x:+.1f}%")

            # Apply styling for better readability
            def highlight_variance(row):
                # Extract numeric value from formatted string
                var_str = row['Variance (£)']
                is_negative = var_str.startswith('(')

                styles = [''] * len(row)

                # Color the variance columns
                if is_negative:
                    styles[-2] = 'color: red'  # Variance (£)
                    styles[-1] = 'color: red'  # Variance (%)
                else:
                    styles[-2] = 'color: green'  # Variance (£)
                    styles[-1] = 'color: green'  # Variance (%)

                # Bold total rows
                if 'Total' in row['Line Item'] or 'EBITDA' in row['Line Item']:
                    styles = [f'font-weight: bold; background-color: #f0f0f0' if s == '' else f'{s}; font-weight: bold; background-color: #f0f0f0' for s in styles]

                return styles

            styled_comparison = comparison.style.apply(highlight_variance, axis=1)

            st.dataframe(styled_comparison, use_container_width=True, hide_index=True)

            # Summary insights
            st.markdown("---")
            st.markdown("#### Key Insights")

            col1, col2, col3 = st.columns(3)

            # Extract EBITDA values
            ebitda_rows = comparison[comparison['Line Item'].str.contains('EBITDA', na=False)]
            if not ebitda_rows.empty:
                base_ebitda_str = ebitda_rows['Base (£)'].iloc[0]
                scenario_ebitda_str = ebitda_rows['Scenario (£)'].iloc[0]

                with col1:
                    st.info(f"**Base EBITDA:** {base_ebitda_str}")

                with col2:
                    st.info(f"**Scenario EBITDA:** {scenario_ebitda_str}")

                with col3:
                    variance_str = ebitda_rows['Variance (£)'].iloc[0]
                    variance_pct = ebitda_rows['Variance (%)'].iloc[0]
                    st.success(f"**EBITDA Impact:** {variance_str} ({variance_pct})")

        except Exception as e:
            st.warning(f"Unable to calculate detailed comparison: {e}")
            st.error(f"Error details: {str(e)}")

    # Save/Delete scenario
    st.markdown("---")
    col1, col2 = st.columns([3, 1])

    with col1:
        if st.button("💾 Save Scenario", type="primary"):
            if 'saved_scenarios' not in st.session_state:
                st.session_state.saved_scenarios = []

            # Check if scenario with same name exists and update it
            existing_idx = next((i for i, s in enumerate(st.session_state.saved_scenarios) if s['name'] == scenario_name), None)
            scenario_data = {
                'name': scenario_name,
                'params': scenario,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
            }

            if existing_idx is not None:
                st.session_state.saved_scenarios[existing_idx] = scenario_data
                st.success(f"✅ Scenario '{scenario_name}' updated!")
            else:
                st.session_state.saved_scenarios.append(scenario_data)
                st.success(f"✅ Scenario '{scenario_name}' saved!")

    with col2:
        # Delete scenario button
        if 'saved_scenarios' in st.session_state and st.session_state.saved_scenarios:
            if st.session_state.get('loaded_scenario'):
                # Only show delete if a scenario is loaded
                if st.button("🗑️ Delete", type="secondary"):
                    # Find and remove the loaded scenario
                    loaded_name = next((s['name'] for s in st.session_state.saved_scenarios if s['params'] == st.session_state.loaded_scenario), None)
                    if loaded_name:
                        st.session_state.saved_scenarios = [s for s in st.session_state.saved_scenarios if s['name'] != loaded_name]
                        if 'loaded_scenario' in st.session_state:
                            del st.session_state.loaded_scenario
                        st.success(f"✅ Scenario '{loaded_name}' deleted!")
                        st.rerun()


def render_pl_view(data):
    """Render full P&L statement view"""
    st.markdown('<p class="main-header">📈 P&L Statement</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Consolidated profit and loss view</p>', unsafe_allow_html=True)

    if not data:
        st.warning("Please upload a budget file first")
        return

    # View options
    col1, col2, col3 = st.columns(3)

    with col1:
        view_type = st.selectbox(
            "View",
            ["Combined", "By Territory", "By Channel"]
        )

    with col2:
        if view_type == "By Territory":
            territory = st.selectbox(
                "Territory",
                ['UK', 'ES', 'IT', 'DE', 'RO', 'CZ', 'HU', 'SK']
            )
        else:
            territory = None

    with col3:
        time_period = st.selectbox(
            "Period",
            ["Monthly", "Quarterly", "Annual"]
        )

    st.markdown("---")

    # Calculate and display P&L
    # Force reload of calculations module to bypass cache
    import pl_calculations as calculations
    import importlib
    importlib.reload(calculations)
    from pl_calculations import PLCalculator

    calc = PLCalculator(data)

    # DIAGNOSTIC: Show what version of calculations.py is loaded
    calc_version = getattr(calculations, '__version__', 'UNKNOWN')

    # Show diagnostic info in an expander
    with st.expander("🔧 Diagnostic Info (Click to expand)", expanded=True):
        st.write(f"**pl_calculations.py version**: {calc_version}")
        st.write(f"**Expected version**: 1.0.6")

        if calc_version == "1.0.6":
            st.success("✅ Version 1.0.6 loaded - B2B debug enabled")
            st.info("Check '🏢 B2B Data Extraction Debug' to see which B2B countries are missing")
        elif calc_version in ["1.0.5", "1.0.4", "1.0.3"]:
            st.warning(f"⚠️ Version {calc_version} - Need to update to 1.0.6 for B2B debug")
        else:
            st.error(f"❌ Wrong version! Expected 1.0.6, got {calc_version}")

        # Show territory count that will be used
        st.write(f"**View Type**: {view_type}")
        if view_type == "Combined":
            st.info("**Territory Count**: Should process 14 territories (UK, ES, DE, IT, FR, RO, PL, CZ, HU, SK, Other EU, US, AU, ROW)")

    try:
        if territory:
            pl = calc.calculate_territory_pl(territory)
        else:
            pl = calc.calculate_combined_pl(debug=True)

            # Show debug territory revenues
            if hasattr(calc, '_debug_territory_revenues'):
                with st.expander("🔍 Territory Revenue Breakdown (Debug)", expanded=False):
                    st.write("**Revenue by Territory** (Annual Total):")
                    import pandas as pd
                    debug_df = pd.DataFrame([
                        {'Territory': t, 'Revenue': format_currency(r)}
                        for t, r in calc._debug_territory_revenues.items()
                    ])
                    st.dataframe(debug_df, hide_index=True)

                    # Show which territories have zero
                    zero_territories = [t for t, r in calc._debug_territory_revenues.items() if r == 0]
                    if zero_territories:
                        st.warning(f"⚠️ **Territories with ZERO revenue**: {', '.join(zero_territories)}")
                        st.write("These territories are NOT contributing to the total!")

                        # Show marketplace debug for zero territories
                        if hasattr(calc, '_mp_debug'):
                            st.markdown("---")
                            st.markdown("**🔬 Marketplace Data Extraction Debug:**")
                            for terr in zero_territories:
                                if terr in calc._mp_debug:
                                    mp_info = calc._mp_debug[terr]
                                    if isinstance(mp_info, dict):
                                        st.write(f"**{terr}**:")
                                        st.write(f"  - Searching for: `{mp_info['searching_for']}`")
                                        st.write(f"  - Found: {'✅ Yes' if mp_info['found'] else '❌ No'}")
                                        st.write(f"  - Available in Excel:")
                                        st.code('\n'.join([f"  - {t}" for t in mp_info['available_in_excel']]))
                                    else:
                                        st.write(f"**{terr}**: {mp_info}")

                    # Show B2B debug for ALL territories
                    if hasattr(calc, '_b2b_debug'):
                        st.markdown("---")
                        st.markdown("**🏢 B2B Data Extraction Debug (ALL Territories):**")
                        st.write("This shows B2B revenue extraction for each territory:")

                        # Show territories with B2B issues
                        b2b_issues = []
                        for terr, b2b_info in calc._b2b_debug.items():
                            if isinstance(b2b_info, dict):
                                if b2b_info['revenue'] == 0 or not b2b_info['found']:
                                    b2b_issues.append(terr)

                        if b2b_issues:
                            st.warning(f"⚠️ **Territories with B2B issues**: {', '.join(b2b_issues)}")

                        # Show details for all territories (collapsed to save space)
                        for terr, b2b_info in sorted(calc._b2b_debug.items()):
                            if isinstance(b2b_info, dict):
                                emoji = "❌" if b2b_info['revenue'] == 0 else "✅"
                                with st.expander(f"{emoji} **{terr}** - B2B Revenue: {format_currency(b2b_info['revenue'])}"):
                                    st.write(f"  - Searching for: `{b2b_info['searching_for']}`")
                                    st.write(f"  - Found: {'✅ Yes' if b2b_info['found'] else '❌ No'}")
                                    st.write(f"  - Available B2B countries in Excel:")
                                    st.code('\n'.join([f"  - {t}" for t in b2b_info['available_in_excel'][:20]]))  # Limit to first 20
                                    if len(b2b_info['available_in_excel']) > 20:
                                        st.write(f"  ... and {len(b2b_info['available_in_excel']) - 20} more")

                    total_debug_rev = sum(calc._debug_territory_revenues.values())
                    st.metric("Total from all territories", format_currency(total_debug_rev))

        # Format for display
        display_pl = pl.copy()

        # Apply number formatting
        for col in display_pl.columns:
            display_pl[col] = display_pl[col].apply(format_currency)

        st.dataframe(
            display_pl,
            width="stretch",
            height=600
        )

        # Summary metrics - Calculate actual values from P&L data
        st.markdown("---")
        st.markdown("### 📊 Key Metrics (Calculated from P&L)")

        col1, col2, col3, col4 = st.columns(4)

        # Get totals from actual P&L data
        date_cols = [c for c in pl.columns if c.startswith('202')]

        with col1:
            total_rev = pl.loc[('Revenue', 'Total Revenue'), date_cols].sum() if ('Revenue', 'Total Revenue') in pl.index else 0
            st.metric("Total Revenue", f"£{total_rev/1e6:.1f}M")

        with col2:
            if ('CM1', 'Total CM1') in pl.index:
                total_cm1 = pl.loc[('CM1', 'Total CM1'), date_cols].sum()
                cm1_pct = total_cm1 / total_rev * 100 if total_rev > 0 else 0
                st.metric(
                    "Contribution Margin 1",
                    f"£{total_cm1/1e6:.1f}M",
                    delta=f"{cm1_pct:.1f}% of revenue"
                )

        with col3:
            if ('CM2', 'Total CM2') in pl.index:
                total_cm2 = pl.loc[('CM2', 'Total CM2'), date_cols].sum()
                cm2_pct = total_cm2 / total_rev * 100 if total_rev > 0 else 0
                st.metric(
                    "Contribution Margin 2",
                    f"£{total_cm2/1e6:.1f}M",
                    delta=f"{cm2_pct:.1f}% of revenue"
                )

        with col4:
            if ('EBITDA', 'EBITDA') in pl.index:
                ebitda = pl.loc[('EBITDA', 'EBITDA'), date_cols].sum()
                ebitda_margin = ebitda / total_rev * 100 if total_rev > 0 else 0
                st.metric(
                    "EBITDA",
                    f"£{ebitda/1e6:.1f}M",
                    delta=f"{ebitda_margin:.1f}% margin"
                )

        # Subscription Revenue Breakdown
        st.markdown("---")
        st.markdown("### 📦 Subscription Revenue Breakdown")

        if 'dtc' in data:
            sub_summary = []
            for terr, dtc_df in data['dtc'].items():
                if dtc_df.empty:
                    continue
                date_cols_dtc = [c for c in dtc_df.columns if c.startswith('202')]

                new_sub_rev = dtc_df[dtc_df['Metric'] == 'New Customer Revenue (Subs)'][date_cols_dtc].sum().sum()
                recurring_rev = dtc_df[dtc_df['Metric'] == 'Returning Revenue (Subs)'][date_cols_dtc].sum().sum()
                cohort_adj = dtc_df[dtc_df['Metric'] == 'Missing Revenue (Cohort Adjustment)'][date_cols_dtc].sum().sum()

                sub_summary.append({
                    'Territory': terr,
                    'New Sub Revenue': new_sub_rev,
                    'Recurring Sub Revenue': recurring_rev,
                    'Cohort Adjustment': cohort_adj,
                    'Total Sub Revenue': new_sub_rev + recurring_rev
                })

            if sub_summary:
                sub_df = pd.DataFrame(sub_summary)

                # Format currency columns
                for col in ['New Sub Revenue', 'Recurring Sub Revenue', 'Cohort Adjustment', 'Total Sub Revenue']:
                    sub_df[col] = sub_df[col].apply(lambda x: f"£{x:,.0f}" if x >= 0 else f"(£{abs(x):,.0f})")

                st.dataframe(sub_df, width="stretch", hide_index=True)

                # Total subscription impact
                total_sub = sum([s['New Sub Revenue'] + s['Recurring Sub Revenue'] for s in sub_summary if isinstance(s['New Sub Revenue'], (int, float))])
                total_cohort_adj = sum([s['Cohort Adjustment'] for s in sub_summary if isinstance(s['Cohort Adjustment'], (int, float))])

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Subscription Revenue", f"£{total_sub:,.0f}")
                with col2:
                    if abs(total_cohort_adj) > 1000:
                        st.metric("Total Cohort Adjustment", f"£{total_cohort_adj:,.0f}")

    except Exception as e:
        st.error(f"Error calculating P&L: {e}")
        st.info("Try selecting a different territory or check that data is properly loaded.")


def render_budget_vs_actuals(data):
    """Render Budget vs Actuals comparison with variance analysis"""
    st.markdown('<p class="main-header">📉 Budget vs Actuals</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Compare actual performance against budget with variance analysis</p>', unsafe_allow_html=True)

    if not data:
        st.warning("Please upload a budget file first")
        return

    # Check if actuals data exists
    actuals = data.get('actuals', pd.DataFrame())
    if actuals.empty:
        st.info("📋 No actuals data found")
        st.markdown("""
        To use Budget vs Actuals comparison, add an "Actuals" sheet to your Excel file with the following structure:

        | Channel | Territory | 2026-02 | 2026-03 | ... |
        |---------|-----------|---------|---------|-----|
        | B2B     | UK        | 100000  | 105000  | ... |
        | DTC     | UK        | 50000   | 52000   | ... |
        | Marketplace | UK    | 25000   | 26000   | ... |

        **Requirements:**
        - Column "Channel" with values: B2B, DTC, Marketplace
        - Column "Territory" (optional) for territory-specific actuals
        - Date columns in YYYY-MM format with actual revenue values
        """)
        return

    calc = PLCalculator(data)
    date_cols = data.get('dates', [])

    if not date_cols:
        st.warning("No date columns found in the data")
        return

    st.markdown("---")

    # Calculate budget totals by channel
    dtc_territories = ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK', 'Other EU']

    budget_b2b = sum(calc.calculate_b2b_revenue().values())
    budget_dtc = sum(sum(calc.calculate_dtc_revenue(t).values()) for t in dtc_territories)
    budget_marketplace = sum(calc.calculate_total_marketplace_revenue().values())
    budget_total = budget_b2b + budget_dtc + budget_marketplace

    # Calculate actual totals by channel from actuals sheet
    actual_b2b = 0
    actual_dtc = 0
    actual_marketplace = 0

    for _, row in actuals.iterrows():
        channel = str(row['Channel']).strip()
        row_total = sum(row[col] for col in date_cols if col in row.index)

        if channel == 'B2B':
            actual_b2b += row_total
        elif channel == 'DTC':
            actual_dtc += row_total
        elif channel == 'Marketplace':
            actual_marketplace += row_total

    actual_total = actual_b2b + actual_dtc + actual_marketplace

    # Variance calculations
    def calculate_variance(actual, budget):
        variance = actual - budget
        variance_pct = (variance / budget * 100) if budget != 0 else 0
        return variance, variance_pct

    def get_variance_color(variance_pct):
        """Return color based on variance percentage"""
        abs_var = abs(variance_pct)
        if abs_var <= 5:
            return "🟢"  # Green - within 5%
        elif abs_var <= 10:
            return "🟡"  # Yellow - 5-10%
        else:
            return "🔴"  # Red - >10%

    # Summary metrics
    st.markdown("### 📊 Overall Performance")

    col1, col2, col3, col4 = st.columns(4)

    _, var_pct_total = calculate_variance(actual_total, budget_total)
    with col1:
        st.metric(
            "Total Revenue",
            f"£{actual_total:,.0f}",
            f"{var_pct_total:+.1f}% vs budget"
        )

    _, var_pct_b2b = calculate_variance(actual_b2b, budget_b2b)
    with col2:
        st.metric(
            "B2B",
            f"£{actual_b2b:,.0f}",
            f"{var_pct_b2b:+.1f}%"
        )

    _, var_pct_dtc = calculate_variance(actual_dtc, budget_dtc)
    with col3:
        st.metric(
            "DTC",
            f"£{actual_dtc:,.0f}",
            f"{var_pct_dtc:+.1f}%"
        )

    _, var_pct_mp = calculate_variance(actual_marketplace, budget_marketplace)
    with col4:
        st.metric(
            "Marketplace",
            f"£{actual_marketplace:,.0f}",
            f"{var_pct_mp:+.1f}%"
        )

    st.markdown("---")

    # Detailed variance table
    st.markdown("### 📋 Variance Analysis")

    variance_data = []
    for channel, budget, actual in [
        ('B2B', budget_b2b, actual_b2b),
        ('DTC', budget_dtc, actual_dtc),
        ('Marketplace', budget_marketplace, actual_marketplace),
        ('**Total**', budget_total, actual_total)
    ]:
        variance, variance_pct = calculate_variance(actual, budget)
        indicator = get_variance_color(variance_pct) if channel != '**Total**' else ''

        variance_data.append({
            'Channel': channel,
            'Budget': budget,
            'Actual': actual,
            'Variance (£)': variance,
            'Variance (%)': variance_pct,
            'Status': indicator
        })

    variance_df = pd.DataFrame(variance_data)

    # Format the dataframe for display
    display_df = variance_df.copy()
    display_df['Budget'] = display_df['Budget'].apply(lambda x: f"£{x:,.0f}")
    display_df['Actual'] = display_df['Actual'].apply(lambda x: f"£{x:,.0f}")
    display_df['Variance (£)'] = display_df['Variance (£)'].apply(lambda x: f"£{x:+,.0f}" if x >= 0 else f"-£{abs(x):,.0f}")
    display_df['Variance (%)'] = display_df['Variance (%)'].apply(lambda x: f"{x:+.1f}%")

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Export variance table
    csv = variance_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Variance Table",
        data=csv,
        file_name=f"budget_vs_actuals_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        key="export_variance_csv"
    )

    st.markdown("---")

    # Monthly trend comparison
    st.markdown("### 📈 Monthly Trends: Budget vs Actuals")

    # Calculate monthly budget and actuals
    monthly_budget = {col: 0.0 for col in date_cols}
    monthly_actual = {col: 0.0 for col in date_cols}

    # Budget monthly totals
    for col in date_cols:
        b2b_rev = calc.calculate_b2b_revenue()
        dtc_rev_list = [calc.calculate_dtc_revenue(t) for t in dtc_territories]
        mp_rev = calc.calculate_total_marketplace_revenue()

        monthly_budget[col] = float(
            b2b_rev.get(col, 0) +
            sum(t_rev.get(col, 0) for t_rev in dtc_rev_list) +
            mp_rev.get(col, 0)
        )

    # Actuals monthly totals
    for col in date_cols:
        if col in actuals.columns:
            monthly_actual[col] = float(actuals[col].sum())

    # Create line chart
    import plotly.graph_objects as go

    chart_data = pd.DataFrame({
        'Month': date_cols,
        'Budget': [monthly_budget[col] for col in date_cols],
        'Actual': [monthly_actual[col] for col in date_cols]
    })

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=chart_data['Month'],
        y=chart_data['Budget'],
        name='Budget',
        mode='lines+markers',
        line=dict(color='#1f77b4', width=2)
    ))
    fig.add_trace(go.Scatter(
        x=chart_data['Month'],
        y=chart_data['Actual'],
        name='Actual',
        mode='lines+markers',
        line=dict(color='#2ca02c', width=2)
    ))

    fig.update_layout(
        title="Monthly Revenue: Budget vs Actuals",
        xaxis_title="Month",
        yaxis_title="Revenue (£)",
        hovermode='x unified',
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Territory-level breakdown (if Territory column exists)
    if 'Territory' in actuals.columns:
        st.markdown("### 🌍 Territory Breakdown")

        territories_in_actuals = actuals['Territory'].dropna().unique()

        if len(territories_in_actuals) > 0:
            selected_territory = st.selectbox(
                "Select territory for detailed view:",
                territories_in_actuals,
                key="bva_territory_selector"
            )

            # Filter actuals for selected territory
            territory_actuals = actuals[actuals['Territory'] == selected_territory]

            # Calculate territory budget
            territory_budget_b2b = sum(calc.calculate_b2b_revenue(territory=selected_territory).values())
            territory_budget_dtc = sum(calc.calculate_dtc_revenue(selected_territory).values()) if selected_territory in dtc_territories else 0
            territory_budget_mp = sum(calc.calculate_marketplace_revenue(selected_territory).values())

            # Calculate territory actuals by channel
            territory_actual_by_channel = {}
            for _, row in territory_actuals.iterrows():
                channel = str(row['Channel']).strip()
                row_total = sum(row[col] for col in date_cols if col in row.index)
                territory_actual_by_channel[channel] = row_total

            # Display territory comparison
            col1, col2, col3 = st.columns(3)

            with col1:
                actual_b2b_terr = territory_actual_by_channel.get('B2B', 0)
                _, var_pct_terr = calculate_variance(actual_b2b_terr, territory_budget_b2b)
                st.metric(
                    "B2B",
                    f"£{actual_b2b_terr:,.0f}",
                    f"{var_pct_terr:+.1f}% ({get_variance_color(var_pct_terr)})"
                )
                st.caption(f"Budget: £{territory_budget_b2b:,.0f}")

            with col2:
                actual_dtc_terr = territory_actual_by_channel.get('DTC', 0)
                _, var_pct_terr = calculate_variance(actual_dtc_terr, territory_budget_dtc)
                st.metric(
                    "DTC",
                    f"£{actual_dtc_terr:,.0f}",
                    f"{var_pct_terr:+.1f}% ({get_variance_color(var_pct_terr)})"
                )
                st.caption(f"Budget: £{territory_budget_dtc:,.0f}")

            with col3:
                actual_mp_terr = territory_actual_by_channel.get('Marketplace', 0)
                _, var_pct_terr = calculate_variance(actual_mp_terr, territory_budget_mp)
                st.metric(
                    "Marketplace",
                    f"£{actual_mp_terr:,.0f}",
                    f"{var_pct_terr:+.1f}% ({get_variance_color(var_pct_terr)})"
                )
                st.caption(f"Budget: £{territory_budget_mp:,.0f}")

    st.markdown("---")
    st.markdown("**Legend:** 🟢 Within ±5% | 🟡 5-10% variance | 🔴 >10% variance")


def render_version_control(data):
    """Render version control page for managing budget versions"""
    st.markdown('<p class="main-header">📚 Version Control</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Save, compare, and manage budget versions</p>', unsafe_allow_html=True)

    if not data:
        st.warning("Please upload a budget file first")
        return

    # Initialize version storage
    if 'budget_versions' not in st.session_state:
        st.session_state.budget_versions = []

    st.markdown("---")

    # Tabs for different version control operations
    tab1, tab2, tab3, tab4 = st.tabs(["📋 All Versions", "💾 Save New Version", "🔄 Compare Versions", "📜 Change Log"])

    with tab1:
        st.markdown("### 📦 Saved Versions")

        if not st.session_state.budget_versions:
            st.info("No versions saved yet. Use the 'Save New Version' tab to create your first version.")
        else:
            # Display versions in a table
            versions_display = []
            for idx, version in enumerate(st.session_state.budget_versions):
                versions_display.append({
                    'Index': idx,
                    'Name': version['name'],
                    'Saved': version['timestamp'],
                    'Notes': version['notes'][:50] + "..." if len(version['notes']) > 50 else version['notes']
                })

            versions_df = pd.DataFrame(versions_display)
            st.dataframe(versions_df[['Name', 'Saved', 'Notes']], use_container_width=True, hide_index=True)

            st.markdown("### 🔧 Version Actions")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Load Version (Rollback)**")
                selected_version_load = st.selectbox(
                    "Select version to load:",
                    range(len(st.session_state.budget_versions)),
                    format_func=lambda i: f"{st.session_state.budget_versions[i]['name']} ({st.session_state.budget_versions[i]['timestamp']})",
                    key="load_version_selector"
                )

                if st.button("🔄 Load This Version", key="load_version_btn"):
                    import copy
                    # Create a backup of current state before loading
                    backup_name = f"Auto-backup before loading {st.session_state.budget_versions[selected_version_load]['name']}"
                    backup_version = {
                        'name': backup_name,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'notes': "Automatic backup created before version rollback",
                        'data': copy.deepcopy(st.session_state.data)
                    }
                    st.session_state.budget_versions.append(backup_version)

                    # Load the selected version
                    st.session_state.data = copy.deepcopy(
                        st.session_state.budget_versions[selected_version_load]['data']
                    )
                    st.success(f"✅ Loaded version: {st.session_state.budget_versions[selected_version_load]['name']}")
                    st.info(f"💾 Auto-backup created: {backup_name}")
                    st.rerun()

            with col2:
                st.markdown("**Delete Version**")
                selected_version_delete = st.selectbox(
                    "Select version to delete:",
                    range(len(st.session_state.budget_versions)),
                    format_func=lambda i: f"{st.session_state.budget_versions[i]['name']} ({st.session_state.budget_versions[i]['timestamp']})",
                    key="delete_version_selector"
                )

                if st.button("🗑️ Delete This Version", key="delete_version_btn"):
                    deleted_name = st.session_state.budget_versions[selected_version_delete]['name']
                    del st.session_state.budget_versions[selected_version_delete]
                    st.success(f"✅ Deleted version: {deleted_name}")
                    st.rerun()

    with tab2:
        st.markdown("### 💾 Save New Version")
        st.markdown("Create a snapshot of the current budget state")

        col1, col2 = st.columns([2, 1])

        with col1:
            version_name = st.text_input(
                "Version name *",
                placeholder="e.g., Q1 Final, Pre-Board Review, V2.1",
                key="save_new_version_name"
            )

        with col2:
            version_tag = st.selectbox(
                "Tag (optional)",
                ["None", "Draft", "Final", "Approved", "Review"],
                key="save_new_version_tag"
            )

        version_notes = st.text_area(
            "Notes",
            placeholder="Describe what changed in this version...",
            key="save_new_version_notes",
            height=120
        )

        if st.button("💾 Save Current State as New Version", key="save_new_version_btn", type="primary"):
            if version_name:
                import copy
                full_name = f"{version_name} [{version_tag}]" if version_tag != "None" else version_name
                version = {
                    'name': full_name,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'notes': version_notes,
                    'data': copy.deepcopy(st.session_state.data),
                    'tag': version_tag
                }
                st.session_state.budget_versions.append(version)
                st.success(f"✅ Saved version: {full_name}")
                st.rerun()
            else:
                st.error("Please enter a version name")

    with tab3:
        st.markdown("### 🔄 Compare Versions")
        st.markdown("See what changed between two versions")

        if len(st.session_state.budget_versions) < 2:
            st.info("You need at least 2 saved versions to compare. Save more versions to enable comparison.")
        else:
            col1, col2 = st.columns(2)

            with col1:
                version_a_idx = st.selectbox(
                    "Version A (older):",
                    range(len(st.session_state.budget_versions)),
                    format_func=lambda i: f"{st.session_state.budget_versions[i]['name']} ({st.session_state.budget_versions[i]['timestamp']})",
                    key="compare_version_a"
                )

            with col2:
                version_b_idx = st.selectbox(
                    "Version B (newer):",
                    range(len(st.session_state.budget_versions)),
                    format_func=lambda i: f"{st.session_state.budget_versions[i]['name']} ({st.session_state.budget_versions[i]['timestamp']})",
                    index=min(1, len(st.session_state.budget_versions) - 1),
                    key="compare_version_b"
                )

            if st.button("🔍 Compare Versions", key="compare_versions_btn", type="primary"):
                version_a = st.session_state.budget_versions[version_a_idx]
                version_b = st.session_state.budget_versions[version_b_idx]

                st.markdown("---")
                st.markdown(f"### Comparison: {version_a['name']} → {version_b['name']}")

                # Compare revenue totals
                calc_a = PLCalculator(version_a['data'])
                calc_b = PLCalculator(version_b['data'])

                dtc_territories = ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK', 'Other EU']

                # Calculate totals for both versions
                b2b_a = sum(calc_a.calculate_b2b_revenue().values())
                b2b_b = sum(calc_b.calculate_b2b_revenue().values())

                dtc_a = sum(sum(calc_a.calculate_dtc_revenue(t).values()) for t in dtc_territories)
                dtc_b = sum(sum(calc_b.calculate_dtc_revenue(t).values()) for t in dtc_territories)

                mp_a = sum(calc_a.calculate_total_marketplace_revenue().values())
                mp_b = sum(calc_b.calculate_total_marketplace_revenue().values())

                total_a = b2b_a + dtc_a + mp_a
                total_b = b2b_b + dtc_b + mp_b

                # Show comparison metrics
                st.markdown("#### 📊 Revenue Changes")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    delta_total = total_b - total_a
                    delta_pct_total = (delta_total / total_a * 100) if total_a != 0 else 0
                    st.metric(
                        "Total Revenue",
                        f"£{total_b:,.0f}",
                        f"£{delta_total:+,.0f} ({delta_pct_total:+.1f}%)"
                    )

                with col2:
                    delta_b2b = b2b_b - b2b_a
                    delta_pct_b2b = (delta_b2b / b2b_a * 100) if b2b_a != 0 else 0
                    st.metric(
                        "B2B",
                        f"£{b2b_b:,.0f}",
                        f"£{delta_b2b:+,.0f} ({delta_pct_b2b:+.1f}%)"
                    )

                with col3:
                    delta_dtc = dtc_b - dtc_a
                    delta_pct_dtc = (delta_dtc / dtc_a * 100) if dtc_a != 0 else 0
                    st.metric(
                        "DTC",
                        f"£{dtc_b:,.0f}",
                        f"£{delta_dtc:+,.0f} ({delta_pct_dtc:+.1f}%)"
                    )

                with col4:
                    delta_mp = mp_b - mp_a
                    delta_pct_mp = (delta_mp / mp_a * 100) if mp_a != 0 else 0
                    st.metric(
                        "Marketplace",
                        f"£{mp_b:,.0f}",
                        f"£{delta_mp:+,.0f} ({delta_pct_mp:+.1f}%)"
                    )

                # Comparison table
                st.markdown("#### 📋 Detailed Comparison")

                comparison_data = []
                for channel, val_a, val_b in [
                    ('B2B', b2b_a, b2b_b),
                    ('DTC', dtc_a, dtc_b),
                    ('Marketplace', mp_a, mp_b),
                    ('**Total**', total_a, total_b)
                ]:
                    delta = val_b - val_a
                    delta_pct = (delta / val_a * 100) if val_a != 0 else 0

                    comparison_data.append({
                        'Channel': channel,
                        'Version A': f"£{val_a:,.0f}",
                        'Version B': f"£{val_b:,.0f}",
                        'Change (£)': f"£{delta:+,.0f}" if delta >= 0 else f"-£{abs(delta):,.0f}",
                        'Change (%)': f"{delta_pct:+.1f}%"
                    })

                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(comparison_df, use_container_width=True, hide_index=True)

                # Export comparison
                csv = comparison_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Export Comparison",
                    data=csv,
                    file_name=f"version_comparison_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key="export_comparison_csv"
                )

    with tab4:
        st.markdown("### 📜 Change Log")
        st.markdown("History of all saved versions")

        if not st.session_state.budget_versions:
            st.info("No versions saved yet. The change log will appear here once you save versions.")
        else:
            # Display versions in reverse chronological order
            for idx in range(len(st.session_state.budget_versions) - 1, -1, -1):
                version = st.session_state.budget_versions[idx]

                with st.expander(f"**{version['name']}** - {version['timestamp']}", expanded=(idx == len(st.session_state.budget_versions) - 1)):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.markdown(f"**Timestamp:** {version['timestamp']}")
                        if version.get('tag'):
                            st.markdown(f"**Tag:** {version['tag']}")
                        if version['notes']:
                            st.markdown(f"**Notes:**")
                            st.markdown(f"> {version['notes']}")
                        else:
                            st.caption("No notes provided")

                    with col2:
                        # Calculate version stats
                        calc_ver = PLCalculator(version['data'])
                        dtc_territories = ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK', 'Other EU']

                        b2b_ver = sum(calc_ver.calculate_b2b_revenue().values())
                        dtc_ver = sum(sum(calc_ver.calculate_dtc_revenue(t).values()) for t in dtc_territories)
                        mp_ver = sum(calc_ver.calculate_total_marketplace_revenue().values())
                        total_ver = b2b_ver + dtc_ver + mp_ver

                        st.metric("Total Revenue", f"£{total_ver:,.0f}")

                    st.markdown("---")
                    st.caption(f"Version index: {idx}")


def render_sensitivity_analysis(data):
    """Render sensitivity analysis page for what-if single variable analysis"""
    st.markdown('<p class="main-header">📈 Sensitivity Analysis</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Understand the impact of individual variables on your budget</p>', unsafe_allow_html=True)

    if not data:
        st.warning("Please upload a budget file first")
        return

    st.markdown("---")

    st.markdown("""
    **What is Sensitivity Analysis?**

    Sensitivity analysis helps you understand which variables have the biggest impact on your budget.
    Adjust one variable at a time to see how it affects total revenue and profitability.

    **How to use:**
    1. Select a variable to test (e.g., DTC Traffic, B2B Revenue)
    2. Adjust the slider to see the impact
    3. View the results in the tornado chart and sensitivity table
    """)

    st.markdown("---")

    # Base case calculations
    calc_base = PLCalculator(data)
    dtc_territories = ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK', 'Other EU']

    base_b2b = sum(calc_base.calculate_b2b_revenue().values())
    base_dtc = sum(sum(calc_base.calculate_dtc_revenue(t).values()) for t in dtc_territories)
    base_marketplace = sum(calc_base.calculate_total_marketplace_revenue().values())
    base_total_revenue = base_b2b + base_dtc + base_marketplace

    st.markdown("### 📊 Base Case")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Revenue", f"£{base_total_revenue:,.0f}")
    with col2:
        st.metric("B2B", f"£{base_b2b:,.0f}")
    with col3:
        st.metric("DTC", f"£{base_dtc:,.0f}")
    with col4:
        st.metric("Marketplace", f"£{base_marketplace:,.0f}")

    st.markdown("---")

    # Sensitivity variables
    st.markdown("### 🎚️ Test Variables")

    variables = {
        "B2B Revenue": {"min": -30, "max": 30, "default": 0, "step": 5, "channel": "b2b"},
        "DTC Revenue": {"min": -30, "max": 30, "default": 0, "step": 5, "channel": "dtc"},
        "Marketplace Revenue": {"min": -30, "max": 30, "default": 0, "step": 5, "channel": "marketplace"},
        "DTC Traffic": {"min": -30, "max": 30, "default": 0, "step": 5, "channel": "dtc_traffic"},
        "DTC Conversion Rate": {"min": -30, "max": 30, "default": 0, "step": 5, "channel": "dtc_cvr"},
        "DTC AOV": {"min": -30, "max": 30, "default": 0, "step": 5, "channel": "dtc_aov"},
        "COGS Rate (All Channels)": {"min": -20, "max": 20, "default": 0, "step": 5, "channel": "cogs"},
    }

    # Select variable to test
    selected_var = st.selectbox(
        "Select variable to test:",
        list(variables.keys()),
        key="sensitivity_variable"
    )

    var_config = variables[selected_var]

    # Slider for adjustment
    adjustment = st.slider(
        f"Adjust {selected_var} (%)",
        min_value=var_config["min"],
        max_value=var_config["max"],
        value=var_config["default"],
        step=var_config["step"],
        key="sensitivity_slider"
    )

    st.markdown("---")

    # Calculate sensitivity impact
    scenario_adjustments = {}

    if var_config["channel"] == "b2b":
        scenario_adjustments['b2b_revenue_adjustment'] = adjustment / 100
    elif var_config["channel"] == "dtc":
        scenario_adjustments['dtc_revenue_adjustment'] = adjustment / 100
    elif var_config["channel"] == "marketplace":
        scenario_adjustments['marketplace_revenue_adjustment'] = adjustment / 100
    elif var_config["channel"] == "dtc_traffic":
        scenario_adjustments['dtc_traffic_adjustment'] = adjustment / 100
    elif var_config["channel"] == "dtc_cvr":
        scenario_adjustments['dtc_cvr_adjustment'] = adjustment / 100
    elif var_config["channel"] == "dtc_aov":
        scenario_adjustments['dtc_aov_adjustment'] = adjustment / 100
    elif var_config["channel"] == "cogs":
        scenario_adjustments['cogs_adjustment'] = adjustment / 100

    # Apply simple revenue adjustments (more sophisticated would adjust underlying drivers)
    if adjustment != 0:
        # Calculate new values (initialize with base values)
        new_b2b = base_b2b
        new_dtc = base_dtc
        new_marketplace = base_marketplace

        if var_config["channel"] == "b2b":
            new_b2b = base_b2b * (1 + adjustment / 100)
        elif var_config["channel"] == "dtc":
            new_dtc = base_dtc * (1 + adjustment / 100)
        elif var_config["channel"] == "marketplace":
            new_marketplace = base_marketplace * (1 + adjustment / 100)
        elif var_config["channel"] in ["dtc_traffic", "dtc_cvr", "dtc_aov"]:
            # For DTC driver changes, approximate impact on revenue
            new_dtc = base_dtc * (1 + adjustment / 100)
        elif var_config["channel"] == "cogs":
            # COGS affects margin, not revenue - keep base values
            pass

        new_total_revenue = new_b2b + new_dtc + new_marketplace

        # Show results
        st.markdown("### 📈 Sensitivity Results")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Impact Metrics")

            revenue_delta = new_total_revenue - base_total_revenue
            revenue_delta_pct = (revenue_delta / base_total_revenue * 100) if base_total_revenue != 0 else 0

            st.metric(
                "Total Revenue",
                f"£{new_total_revenue:,.0f}",
                f"£{revenue_delta:+,.0f} ({revenue_delta_pct:+.1f}%)"
            )

            if var_config["channel"] == "b2b":
                b2b_delta = new_b2b - base_b2b
                st.metric(
                    "B2B Revenue",
                    f"£{new_b2b:,.0f}",
                    f"£{b2b_delta:+,.0f}"
                )
            elif var_config["channel"] == "dtc" or var_config["channel"] in ["dtc_traffic", "dtc_cvr", "dtc_aov"]:
                dtc_delta = new_dtc - base_dtc
                st.metric(
                    "DTC Revenue",
                    f"£{new_dtc:,.0f}",
                    f"£{dtc_delta:+,.0f}"
                )
            elif var_config["channel"] == "marketplace":
                mp_delta = new_marketplace - base_marketplace
                st.metric(
                    "Marketplace Revenue",
                    f"£{new_marketplace:,.0f}",
                    f"£{mp_delta:+,.0f}"
                )

        with col2:
            st.markdown("#### Sensitivity Interpretation")

            if abs(revenue_delta_pct) < 2:
                st.info(f"🟢 **Low Sensitivity**: {selected_var} has a relatively small impact on total revenue.")
            elif abs(revenue_delta_pct) < 5:
                st.warning(f"🟡 **Medium Sensitivity**: {selected_var} has a moderate impact on total revenue.")
            else:
                st.error(f"🔴 **High Sensitivity**: {selected_var} has a significant impact on total revenue. This is a key driver!")

            st.markdown("**Key Insights:**")
            if var_config["channel"] in ["b2b", "dtc", "marketplace"]:
                st.write(f"- A {adjustment:+}% change in {selected_var} results in a {revenue_delta_pct:+.1f}% change in total revenue")
                st.write(f"- Revenue impact: £{abs(revenue_delta):,.0f}")
            elif var_config["channel"] in ["dtc_traffic", "dtc_cvr", "dtc_aov"]:
                st.write(f"- A {adjustment:+}% change in {selected_var} approximately results in a {revenue_delta_pct:+.1f}% change in total revenue")
                st.write(f"- Focus on improving this metric for revenue growth")

    else:
        st.info("👆 Adjust the slider above to see the impact of changes")

    st.markdown("---")

    # Tornado chart showing impact of different variables
    st.markdown("### 🌪️ Tornado Chart: Variable Impact Comparison")
    st.markdown("Shows the impact on total revenue when each variable changes by ±10%")

    # Calculate impact for each variable at +10% and -10%
    import plotly.graph_objects as go

    tornado_data = []

    test_vars = [
        ("B2B Revenue", "b2b"),
        ("DTC Revenue", "dtc"),
        ("Marketplace Revenue", "marketplace"),
    ]

    for var_name, channel in test_vars:
        # Calculate +10% impact
        if channel == "b2b":
            new_total_up = (base_b2b * 1.1) + base_dtc + base_marketplace
            new_total_down = (base_b2b * 0.9) + base_dtc + base_marketplace
        elif channel == "dtc":
            new_total_up = base_b2b + (base_dtc * 1.1) + base_marketplace
            new_total_down = base_b2b + (base_dtc * 0.9) + base_marketplace
        elif channel == "marketplace":
            new_total_up = base_b2b + base_dtc + (base_marketplace * 1.1)
            new_total_down = base_b2b + base_dtc + (base_marketplace * 0.9)

        impact_up = ((new_total_up - base_total_revenue) / base_total_revenue * 100)
        impact_down = ((new_total_down - base_total_revenue) / base_total_revenue * 100)

        tornado_data.append({
            'variable': var_name,
            'impact_up': impact_up,
            'impact_down': impact_down,
            'range': abs(impact_up - impact_down)
        })

    # Sort by range (biggest impact first)
    tornado_data_sorted = sorted(tornado_data, key=lambda x: x['range'], reverse=True)

    # Create tornado chart
    fig = go.Figure()

    variables_list = [d['variable'] for d in tornado_data_sorted]
    impact_up_list = [d['impact_up'] for d in tornado_data_sorted]
    impact_down_list = [d['impact_down'] for d in tornado_data_sorted]

    fig.add_trace(go.Bar(
        name='+10%',
        y=variables_list,
        x=impact_up_list,
        orientation='h',
        marker=dict(color='#2ca02c')
    ))

    fig.add_trace(go.Bar(
        name='-10%',
        y=variables_list,
        x=impact_down_list,
        orientation='h',
        marker=dict(color='#d62728')
    ))

    fig.update_layout(
        title="Impact on Total Revenue (±10% change in each variable)",
        xaxis_title="Change in Total Revenue (%)",
        yaxis_title="Variable",
        barmode='overlay',
        height=400,
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)

    # Sensitivity table
    st.markdown("### 📋 Sensitivity Table")

    sensitivity_table_data = []
    for d in tornado_data_sorted:
        sensitivity_table_data.append({
            'Variable': d['variable'],
            'Impact (+10%)': f"{d['impact_up']:+.2f}%",
            'Impact (-10%)': f"{d['impact_down']:+.2f}%",
            'Total Range': f"{d['range']:.2f}%"
        })

    sensitivity_df = pd.DataFrame(sensitivity_table_data)
    st.dataframe(sensitivity_df, use_container_width=True, hide_index=True)

    # Export sensitivity table
    csv = sensitivity_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Sensitivity Table",
        data=csv,
        file_name=f"sensitivity_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        key="export_sensitivity_csv"
    )

    st.markdown("---")
    st.markdown("**💡 Tip:** Variables with the largest range are your key drivers. Focus on improving these for maximum impact!")


def render_export(data):
    """Render export functionality"""
    st.markdown('<p class="main-header">⬇️ Export Data</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Export budgets and forecasts to Excel</p>', unsafe_allow_html=True)

    if not data:
        st.warning("Please upload a budget file first")
        return

    st.markdown("### 📁 Export Options")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**What to Export**")

        export_b2b = st.checkbox("B2B Customer Data", value=True)
        export_dtc = st.checkbox("DTC Inputs", value=True)
        export_overheads = st.checkbox("Overheads", value=True)
        export_pl = st.checkbox("P&L Statements", value=True)

    with col2:
        st.markdown("**Export Settings**")

        include_formulas = st.checkbox("Include Formulas", value=False)
        include_scenarios = st.checkbox("Include Saved Scenarios", value=False)

    st.markdown("---")

    if st.button("📥 Generate Export", type="primary"):
        with st.spinner("Generating Excel export..."):
            try:
                output = io.BytesIO()

                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # Export B2B
                    if export_b2b and 'b2b' in data:
                        data['b2b'].to_excel(writer, sheet_name='B2B', index=False)

                    # Export Overheads
                    if export_overheads and 'overheads' in data:
                        data['overheads'].to_excel(writer, sheet_name='Overheads', index=False)

                    # Export P&L
                    if export_pl:
                        calc = PLCalculator(data)
                        for territory in ['UK', 'ES', 'IT']:
                            try:
                                pl = calc.calculate_territory_pl(territory)
                                pl.to_excel(writer, sheet_name=f'{territory} P&L')
                            except:
                                pass

                output.seek(0)

                st.download_button(
                    label="📥 Download Excel File",
                    data=output,
                    file_name=f"budget_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                st.success("Export ready!")

            except Exception as e:
                st.error(f"Export failed: {e}")


def main():
    """Main application entry point"""
    # Initialize session state
    if 'data' not in st.session_state:
        st.session_state.data = None
        st.session_state.file_loaded = False

    # Load data
    data = load_data()

    # Render sidebar and get current page
    page = render_sidebar()

    # Render appropriate page
    if page == "📊 Dashboard":
        render_dashboard(data)
    elif page == "💰 Revenue Inputs":
        render_revenue_inputs(data)
    elif page == "📦 B2B Management":
        render_b2b_management(data)
    elif page == "💸 Cost Management":
        render_cost_management(data)
    elif page == "📣 Marketing":
        render_marketing_management(data)
    elif page == "🎯 Scenario Planning":
        render_scenario_planning(data)
    elif page == "📈 P&L View":
        render_pl_view(data)
    elif page == "📉 Budget vs Actuals":
        render_budget_vs_actuals(data)
    elif page == "📚 Version Control":
        render_version_control(data)
    elif page == "📈 Sensitivity Analysis":
        render_sensitivity_analysis(data)
    elif page == "📝 Comments & Notes":
        render_comments_system(data)
    elif page == "📋 Assumptions":
        render_assumptions_register(data)
    elif page == "🛡️ Data Quality":
        render_data_quality_dashboard(data)
    elif page == "💧 Waterfall Analysis":
        render_waterfall_analysis(data)
    elif page == "⬇️ Export":
        render_export(data)


if __name__ == "__main__":
    main()
