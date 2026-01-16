"""
Budget Planning & Forecasting App
A Streamlit application for FY26-27 budget management
"""
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import io
from datetime import datetime

# Import our modules
from data_loader import load_all_data, BudgetDataLoader
from calculations import PLCalculator, format_currency, format_percentage

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
        st.markdown("---")

        # Navigation
        page = st.radio(
            "Navigate to",
            ["📊 Dashboard", "💰 Revenue Inputs", "📦 B2B Management",
             "💸 Cost Management", "🎯 Scenario Planning", "📈 P&L View", "⬇️ Export"],
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
    dtc_territories = ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK']
    dtc_total = sum(
        sum(calc.calculate_dtc_revenue(territory).values())
        for territory in dtc_territories
    )

    # Calculate Marketplace total across all territories
    marketplace_total = sum(
        sum(calc.calculate_marketplace_revenue(territory).values())
        for territory in dtc_territories
    )

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
        # Channel revenue table
        channel_table = pd.DataFrame({
            'Channel': ['B2B', 'DTC', 'Marketplace', 'Total'],
            'Revenue': [b2b_total, dtc_total, marketplace_total, total_revenue],
            '% of Total': [
                f"{(b2b_total/total_revenue)*100:.1f}%" if total_revenue > 0 else "0%",
                f"{(dtc_total/total_revenue)*100:.1f}%" if total_revenue > 0 else "0%",
                f"{(marketplace_total/total_revenue)*100:.1f}%" if total_revenue > 0 else "0%",
                "100.0%"
            ]
        })
        channel_table['Revenue'] = channel_table['Revenue'].apply(lambda x: f"£{x:,.0f}")
        st.dataframe(channel_table, hide_index=True, use_container_width=True)

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
            # Aggregate Marketplace revenue across all territories by month
            monthly_marketplace = {}
            for territory in dtc_territories:
                territory_revenue = calc.calculate_marketplace_revenue(territory)
                for month, revenue in territory_revenue.items():
                    monthly_marketplace[month] = monthly_marketplace.get(month, 0) + revenue

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

    dtc_territories = ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK']
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

                # Customers
                customers_row = dtc_df[dtc_df['Metric'] == 'New Customers']
                if not customers_row.empty:
                    total_customers += customers_row[date_cols].sum().sum()

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
        ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK'],
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

                if st.button("💾 Save Changes", key=f"save_dtc_{territory}"):
                    # Update session state with edited DTC data
                    # Merge edited inputs back with calculated metrics
                    full_df = pd.concat([edited_df, calculated_df])
                    full_df['Territory'] = territory
                    full_df = full_df.reset_index()

                    # Update session state
                    st.session_state.data['dtc'][territory] = full_df
                    st.success(f"✅ Changes saved for {territory}!")

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
            customers_row = dtc_df[dtc_df['Metric'] == 'New Customers']
            if not customers_row.empty:
                base_customers = customers_row[date_cols].sum().sum()

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

    col1, col2 = st.columns([1, 4])
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

        scenario_name = st.text_input("Scenario Name", value="Optimistic Growth")

    st.markdown("---")

    # Adjustment sliders
    st.markdown("### 🎛️ Scenario Adjustments")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Revenue Drivers**")

        dtc_growth = st.slider("DTC Revenue Growth %", -30, 50, 10, key="sc_dtc")
        b2b_growth = st.slider("B2B Revenue Growth %", -30, 50, 5, key="sc_b2b")
        mp_growth = st.slider("Marketplace Growth %", -30, 50, 15, key="sc_mp")

    with col2:
        st.markdown("**Margin Impacts**")

        cogs_change = st.slider("CoGS Rate Change (pp)", -5.0, 5.0, 0.0, step=0.5, key="sc_cogs")
        fulfilment_change = st.slider("Fulfilment Rate Change (pp)", -5.0, 5.0, 0.0, step=0.5, key="sc_ful")

    with col3:
        st.markdown("**Cost Assumptions**")

        marketing_change = st.slider("Marketing Spend %", -30, 50, 0, key="sc_mkt")
        overhead_change = st.slider("Overhead Change %", -20, 30, 0, key="sc_oh")

    # Build scenario
    scenario = {
        'dtc_revenue_UK': dtc_growth,
        'dtc_revenue_ES': dtc_growth,
        'dtc_revenue_IT': dtc_growth,
        'b2b_growth': b2b_growth,
        'mp_growth': mp_growth,
        'cogs_change': cogs_change,
        'fulfilment_change': fulfilment_change,
    }

    st.markdown("---")

    # Results comparison
    st.markdown("### 📈 Scenario Comparison")

    calc = PLCalculator(data, scenario)
    base_calc = PLCalculator(data, {})

    # Calculate all channel revenues
    dtc_territories = ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK']

    # Base case
    base_b2b = sum(base_calc.calculate_b2b_revenue().values())
    base_dtc = sum(
        sum(base_calc.calculate_dtc_revenue(territory).values())
        for territory in dtc_territories
    )
    base_marketplace = sum(
        sum(base_calc.calculate_marketplace_revenue(territory).values())
        for territory in dtc_territories
    )
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

    # Save scenario
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if st.button("💾 Save Scenario", type="primary"):
            if 'saved_scenarios' not in st.session_state:
                st.session_state.saved_scenarios = []
            st.session_state.saved_scenarios.append({
                'name': scenario_name,
                'params': scenario,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            st.success(f"Scenario '{scenario_name}' saved!")


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
    calc = PLCalculator(data)

    try:
        if territory:
            pl = calc.calculate_territory_pl(territory)
        else:
            pl = calc.calculate_combined_pl()

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
    elif page == "🎯 Scenario Planning":
        render_scenario_planning(data)
    elif page == "📈 P&L View":
        render_pl_view(data)
    elif page == "⬇️ Export":
        render_export(data)


if __name__ == "__main__":
    main()
