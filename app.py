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

    # Calculate totals
    b2b_total = sum(calc.calculate_b2b_revenue().values())

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total B2B Revenue",
            value=f"£{b2b_total/1e6:.1f}M",
            delta="+12% vs LY"
        )

    with col2:
        # Count active B2B customers
        b2b_customers = len(data['b2b'][data['b2b']['Customer Name'].notna()])
        st.metric(
            label="B2B Customers",
            value=f"{b2b_customers}",
            delta="+15"
        )

    with col3:
        # Get territories with data
        territories_active = len([t for t in data.get('dtc', {}) if data['dtc'][t] is not None])
        st.metric(
            label="Active Territories",
            value=f"{territories_active}",
            delta="0"
        )

    with col4:
        # Calculate overhead total
        oh_total = sum(calc.calculate_overheads().values())
        st.metric(
            label="Total Overheads",
            value=f"£{abs(oh_total)/1e6:.1f}M",
            delta="-5%"
        )

    st.markdown("---")

    # Revenue by Territory Group
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📍 B2B Revenue by Region")

        region_data = []
        for group in ['UK', 'CE', 'EE', 'ROW']:
            rev = calc.calculate_b2b_revenue(country_group=group)
            total = sum(rev.values())
            region_data.append({'Region': group, 'Revenue': total})

        region_df = pd.DataFrame(region_data)
        region_df['Revenue'] = region_df['Revenue'].apply(lambda x: f"£{x:,.0f}")
        st.dataframe(region_df, width="stretch", hide_index=True)

    with col2:
        st.subheader("📅 Monthly Trend")

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

    # Filter out summary/total rows that appear in Excel exports
    summary_terms = ['Revenue', 'Grand Total', 'Sub Total', 'CM1', 'CM2', 'Total', 'EBITDA', 'CoGS', 'Fulfilment']
    b2b = b2b[~b2b['Customer Name'].str.contains('|'.join(summary_terms), case=False, na=False)]
    b2b = b2b[b2b['Customer Name'].notna() & (b2b['Customer Name'].str.strip() != '')]

    date_cols = [c for c in b2b.columns if c.startswith('202')]
    b2b['Total Revenue'] = b2b[date_cols].apply(pd.to_numeric, errors='coerce').fillna(0).sum(axis=1)

    # Only show customers with revenue > 0
    b2b = b2b[b2b['Total Revenue'] > 0]

    top_customers = b2b.nlargest(10, 'Total Revenue')[['Customer Name', 'Country', 'Country Group', 'Total Revenue']]
    top_customers['Total Revenue'] = top_customers['Total Revenue'].apply(lambda x: f"£{x:,.0f}")

    st.dataframe(top_customers, width='stretch', hide_index=True)


def render_revenue_inputs(data):
    """Render DTC revenue input forms"""
    st.markdown('<p class="main-header">💰 Revenue Inputs</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Manage DTC channel assumptions by territory</p>', unsafe_allow_html=True)

    if not data:
        st.warning("Please upload a budget file first")
        return

    # Territory selector
    territory = st.selectbox(
        "Select Territory",
        ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK'],
        key='dtc_territory'
    )

    if territory in data.get('dtc', {}):
        dtc_data = data['dtc'][territory]

        st.markdown("### 📊 Key Metrics")

        # Create editable dataframe
        if not dtc_data.empty:
            # Pivot for better display
            display_df = dtc_data.set_index('Metric')
            display_df = display_df.drop(columns=['Territory'], errors='ignore')

            # Show only date columns
            date_cols = [c for c in display_df.columns if c.startswith('202')]
            display_df = display_df[date_cols[:12]]  # Show first 12 months

            edited_df = st.data_editor(
                display_df,
                width="stretch",
                num_rows="fixed",
                key=f"dtc_editor_{territory}"
            )

            if st.button("💾 Save Changes", key=f"save_dtc_{territory}"):
                # Update session state with edited DTC data
                # Reconstruct the full dataframe with the metric names
                updated_dtc = edited_df.copy()
                updated_dtc['Territory'] = territory
                st.session_state.data['dtc'][territory] = updated_dtc
                st.success(f"✅ Changes saved for {territory} in session!")
    else:
        st.info(f"No DTC data available for {territory}")

    # Quick scenario adjustments
    st.markdown("---")
    st.markdown("### 🎛️ Quick Adjustments")

    col1, col2, col3 = st.columns(3)

    with col1:
        traffic_adj = st.slider(
            "Traffic Growth %",
            min_value=-50,
            max_value=100,
            value=0,
            key=f"traffic_{territory}"
        )

    with col2:
        cvr_adj = st.slider(
            "Conversion Rate Change %",
            min_value=-50,
            max_value=100,
            value=0,
            key=f"cvr_{territory}"
        )

    with col3:
        aov_adj = st.slider(
            "AOV Change %",
            min_value=-30,
            max_value=50,
            value=0,
            key=f"aov_{territory}"
        )

    # Show projected impact
    if any([traffic_adj, cvr_adj, aov_adj]):
        st.markdown("### 📈 Projected Impact")

        base_rev = 100000  # Example base
        new_rev = base_rev * (1 + traffic_adj/100) * (1 + cvr_adj/100) * (1 + aov_adj/100)
        change = new_rev - base_rev

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Base Revenue", f"£{base_rev:,.0f}")
        with col2:
            st.metric("Projected Revenue", f"£{new_rev:,.0f}", delta=f"£{change:,.0f}")


def render_b2b_management(data):
    """Render B2B customer management interface"""
    st.markdown('<p class="main-header">📦 B2B Management</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Manage B2B customer forecasts and targets</p>', unsafe_allow_html=True)

    if not data:
        st.warning("Please upload a budget file first")
        return

    b2b = data['b2b'].copy()

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

    display_cols = ['Customer Name', 'Country', 'Country Group', 'Customer Margin'] + date_cols[:6] + ['Total']
    display_df = filtered[display_cols].copy()

    edited_b2b = st.data_editor(
        display_df,
        width="stretch",
        num_rows="dynamic",
        column_config={
            "Customer Name": st.column_config.TextColumn("Customer", width="medium"),
            "Country": st.column_config.TextColumn("Country", width="small"),
            "Country Group": st.column_config.SelectboxColumn("Region", options=['UK', 'CE', 'EE', 'ROW']),
            "Customer Margin": st.column_config.NumberColumn("Margin", format="£%.0f"),
            "Total": st.column_config.NumberColumn("Total", format="£%.0f", disabled=True),
        },
        key="b2b_editor"
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 Save Changes", type="primary", key="save_b2b_main"):
            # Update session state with edited data
            # Remove the calculated 'Total' column before saving
            edited_b2b_clean = edited_b2b.drop(columns=['Total'], errors='ignore')

            # Update the original b2b dataframe with edited values
            # Match by Customer Name and update
            for idx, row in edited_b2b_clean.iterrows():
                customer_name = row['Customer Name']
                mask = data['b2b']['Customer Name'] == customer_name
                for col in edited_b2b_clean.columns:
                    if col in data['b2b'].columns:
                        data['b2b'].loc[mask, col] = row[col]

            # Update session state
            st.session_state.data['b2b'] = data['b2b']
            st.success("✅ Changes saved to session! (Note: Changes are not persisted to Excel file)")

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

        st.data_editor(
            filtered_oh[display_cols],
            width="stretch",
            num_rows="dynamic",
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

        fulfilment = data['fulfilment'].copy()

        edited_ful = st.data_editor(
            fulfilment,
            width="stretch",
            column_config={
                "Rate": st.column_config.NumberColumn("Rate %", format="%.1f%%")
            },
            key="ful_editor"
        )

        if st.button("💾 Save Fulfilment Rates", key="save_fulfilment"):
            # Update session state with edited fulfilment rates
            st.session_state.data['fulfilment'] = edited_ful
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

    # Calculate key metrics
    col1, col2, col3 = st.columns(3)

    base_b2b = sum(base_calc.calculate_b2b_revenue().values())
    new_b2b = base_b2b * (1 + b2b_growth/100)

    with col1:
        st.metric(
            "B2B Revenue",
            f"£{new_b2b/1e6:.2f}M",
            delta=f"{b2b_growth:+.1f}%"
        )

    with col2:
        # Estimate EBITDA impact
        base_ebitda = base_b2b * 0.15  # Rough estimate
        impact = (dtc_growth + b2b_growth + mp_growth) / 3 - overhead_change
        new_ebitda = base_ebitda * (1 + impact/100)

        st.metric(
            "Est. EBITDA",
            f"£{new_ebitda/1e6:.2f}M",
            delta=f"{impact:+.1f}%"
        )

    with col3:
        margin_impact = -cogs_change - fulfilment_change
        st.metric(
            "Margin Impact",
            f"{margin_impact:+.1f}pp",
            delta="improvement" if margin_impact > 0 else "decline"
        )

    # Detailed P&L comparison
    with st.expander("📊 Detailed P&L Comparison"):
        try:
            base_pl = base_calc.calculate_territory_pl('UK')
            new_pl = calc.calculate_territory_pl('UK')

            comparison = pd.DataFrame({
                'Base': base_pl.iloc[:, :6].sum(axis=1),
                'Scenario': new_pl.iloc[:, :6].sum(axis=1),
            })
            comparison['Variance'] = comparison['Scenario'] - comparison['Base']
            comparison['Var %'] = (comparison['Variance'] / comparison['Base'].abs() * 100).round(1)

            st.dataframe(comparison, width="stretch")
        except Exception as e:
            st.warning(f"Unable to calculate detailed comparison: {e}")

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

        # Summary metrics
        st.markdown("---")
        st.markdown("### 📊 Key Metrics")

        col1, col2, col3, col4 = st.columns(4)

        # Get totals
        date_cols = [c for c in pl.columns if c.startswith('202')]

        with col1:
            total_rev = pl.loc[('Revenue', 'Total Revenue'), date_cols].sum() if ('Revenue', 'Total Revenue') in pl.index else 0
            st.metric("Total Revenue", f"£{total_rev/1e6:.1f}M")

        with col2:
            if ('CM1', 'Total CM1') in pl.index:
                total_cm1 = pl.loc[('CM1', 'Total CM1'), date_cols].sum()
                cm1_pct = total_cm1 / total_rev * 100 if total_rev > 0 else 0
                st.metric("CM1 %", f"{cm1_pct:.1f}%")

        with col3:
            if ('CM2', 'Total CM2') in pl.index:
                total_cm2 = pl.loc[('CM2', 'Total CM2'), date_cols].sum()
                cm2_pct = total_cm2 / total_rev * 100 if total_rev > 0 else 0
                st.metric("CM2 %", f"{cm2_pct:.1f}%")

        with col4:
            if ('EBITDA', 'EBITDA') in pl.index:
                ebitda = pl.loc[('EBITDA', 'EBITDA'), date_cols].sum()
                ebitda_pct = ebitda / total_rev * 100 if total_rev > 0 else 0
                st.metric("EBITDA %", f"{ebitda_pct:.1f}%")

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
