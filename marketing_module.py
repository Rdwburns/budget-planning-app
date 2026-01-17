"""
Marketing Management Module
Dedicated view for managing and analyzing marketing spend across channels and territories
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from calculations import PLCalculator, format_currency


def render_marketing_management(data):
    """
    Marketing Management Page
    View and analyze marketing spend by territory, channel, and time period
    """
    st.markdown('<p class="main-header">📣 Marketing Management</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Analyze marketing spend and ROI across territories</p>', unsafe_allow_html=True)

    if not data:
        st.warning("Please upload a budget file first")
        return

    calc = PLCalculator(data)

    # Extract marketing data from DTC inputs and overheads
    marketing_data = {}
    dtc_territories = ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK', 'Other EU']

    # Get DTC marketing budgets
    for territory in dtc_territories:
        if territory in data.get('dtc', {}):
            dtc_data = data['dtc'][territory]
            marketing_row = dtc_data[dtc_data['Metric'] == 'Marketing Budget']

            if not marketing_row.empty:
                marketing_budget = {}
                for col in data.get('dates', []):
                    if col in marketing_row.columns:
                        val = float(marketing_row[col].iloc[0]) if len(marketing_row) > 0 else 0
                        marketing_budget[col] = val

                if sum(marketing_budget.values()) > 0:
                    marketing_data[territory] = {
                        'budget': marketing_budget,
                        'channel': 'DTC'
                    }

    # Get marketing from overheads (central marketing)
    oh = data.get('overheads', pd.DataFrame())
    if not oh.empty and 'Function' in oh.columns:
        marketing_oh = oh[oh['Function'].str.contains('Marketing', case=False, na=False)]

        if not marketing_oh.empty:
            central_marketing = {}
            for col in data.get('dates', []):
                if col in marketing_oh.columns:
                    val = pd.to_numeric(marketing_oh[col], errors='coerce').sum()
                    central_marketing[col] = abs(val)  # Make positive for display

            if sum(central_marketing.values()) > 0:
                marketing_data['Central'] = {
                    'budget': central_marketing,
                    'channel': 'Group'
                }

    if not marketing_data:
        st.warning("No marketing data found in budget. Marketing budget should be in DTC territory sheets or Overheads.")
        return

    # Total marketing spend
    st.markdown("### 📊 Marketing Overview")

    total_marketing = {}
    for col in data.get('dates', []):
        total = sum(
            territory_data['budget'].get(col, 0)
            for territory_data in marketing_data.values()
        )
        total_marketing[col] = total

    annual_marketing = sum(total_marketing.values())

    # Calculate revenue for ROI
    b2b_total = sum(calc.calculate_b2b_revenue().values())
    dtc_total = sum(sum(calc.calculate_dtc_revenue(t).values()) for t in dtc_territories if t in data.get('dtc', {}))
    mp_total = sum(calc.calculate_total_marketplace_revenue().values())
    total_revenue = b2b_total + dtc_total + mp_total

    marketing_pct = (annual_marketing / total_revenue * 100) if total_revenue > 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Marketing Budget",
            format_currency(annual_marketing),
            f"{marketing_pct:.1f}% of revenue"
        )

    with col2:
        avg_monthly = annual_marketing / 12 if annual_marketing > 0 else 0
        st.metric("Avg Monthly Spend", format_currency(avg_monthly))

    with col3:
        roi = total_revenue / annual_marketing if annual_marketing > 0 else 0
        st.metric("Revenue per £1 Marketing", f"£{roi:.2f}")

    with col4:
        territories_with_marketing = len([t for t in marketing_data.keys() if t != 'Central'])
        st.metric("Territories with Marketing", territories_with_marketing)

    st.markdown("---")

    # Marketing spend by territory
    st.markdown("### 🌍 Marketing Spend by Territory")

    # Build territory spend dataframe
    territory_spend = []
    for territory, data_dict in marketing_data.items():
        annual_spend = sum(data_dict['budget'].values())
        territory_spend.append({
            'Territory': territory,
            'Annual Spend': annual_spend,
            'Channel': data_dict['channel']
        })

    territory_df = pd.DataFrame(territory_spend).sort_values('Annual Spend', ascending=False)

    # Bar chart
    fig = px.bar(
        territory_df,
        x='Territory',
        y='Annual Spend',
        text=territory_df['Annual Spend'].apply(lambda x: format_currency(x)),
        color='Channel',
        title='Annual Marketing Spend by Territory'
    )

    fig.update_layout(
        yaxis_title="Marketing Spend (£)",
        height=400
    )

    fig.update_traces(textposition='outside')

    st.plotly_chart(fig, use_container_width=True)

    # Table view
    with st.expander("📋 Detailed Territory Breakdown", expanded=False):
        territory_df['Annual Spend'] = territory_df['Annual Spend'].apply(format_currency)

        # Add percentage
        territory_df['% of Total'] = [
            f"{(sum(marketing_data[t]['budget'].values()) / annual_marketing * 100):.1f}%"
            for t in territory_df['Territory']
        ]

        st.dataframe(territory_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Monthly trend
    st.markdown("### 📈 Marketing Spend Trend")

    col1, col2 = st.columns([3, 1])

    with col2:
        view_territories = st.multiselect(
            "Select Territories",
            list(marketing_data.keys()),
            default=list(marketing_data.keys())[:5] if len(marketing_data) > 5 else list(marketing_data.keys())
        )

    # Build monthly trend data
    monthly_data = []
    for territory in view_territories:
        if territory in marketing_data:
            for month, value in marketing_data[territory]['budget'].items():
                monthly_data.append({
                    'Month': month,
                    'Territory': territory,
                    'Spend': value
                })

    if monthly_data:
        monthly_df = pd.DataFrame(monthly_data)

        fig = px.line(
            monthly_df,
            x='Month',
            y='Spend',
            color='Territory',
            title='Monthly Marketing Spend Trend',
            markers=True
        )

        fig.update_layout(
            yaxis_title="Marketing Spend (£)",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Marketing ROI Analysis
    st.markdown("### 💰 Marketing ROI Analysis")

    st.info("💡 **ROI Calculation**: Revenue per £1 of marketing spend by territory")

    # Calculate ROI by territory
    roi_data = []
    for territory in dtc_territories:
        if territory in marketing_data:
            territory_marketing = sum(marketing_data[territory]['budget'].values())
            territory_revenue = sum(calc.calculate_dtc_revenue(territory).values())

            if territory_marketing > 0:
                roi = territory_revenue / territory_marketing
                roi_data.append({
                    'Territory': territory,
                    'Marketing Spend': territory_marketing,
                    'Revenue': territory_revenue,
                    'ROI': roi,
                    'ROI Text': f"£{roi:.2f}"
                })

    if roi_data:
        roi_df = pd.DataFrame(roi_data).sort_values('ROI', ascending=False)

        col1, col2 = st.columns(2)

        with col1:
            # ROI bar chart
            fig = px.bar(
                roi_df,
                x='Territory',
                y='ROI',
                text='ROI Text',
                title='Revenue per £1 Marketing Spend',
                color='ROI',
                color_continuous_scale='Greens'
            )

            fig.update_layout(
                yaxis_title="ROI (£ Revenue / £1 Marketing)",
                height=400,
                showlegend=False
            )

            fig.update_traces(textposition='outside')

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Efficiency table
            st.markdown("#### 🎯 Marketing Efficiency")

            roi_df['Marketing Spend'] = roi_df['Marketing Spend'].apply(format_currency)
            roi_df['Revenue'] = roi_df['Revenue'].apply(format_currency)

            display_df = roi_df[['Territory', 'Marketing Spend', 'Revenue', 'ROI Text']].copy()
            display_df.columns = ['Territory', 'Marketing', 'Revenue', 'ROI']

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Insights
            best_roi = roi_df.iloc[0]['Territory']
            best_roi_val = roi_df.iloc[0]['ROI']
            st.success(f"🏆 **Best ROI**: {best_roi} generates £{best_roi_val:.2f} revenue per £1 marketing")

    st.markdown("---")

    # Scenario modeling
    st.markdown("### 🎯 Marketing Budget Scenarios")

    st.info("💡 Model the impact of changing marketing spend")

    col1, col2, col3 = st.columns(3)

    with col1:
        scenario_change = st.slider(
            "Change Marketing Budget",
            min_value=-50,
            max_value=100,
            value=0,
            step=5,
            format="%d%%"
        )

    with col2:
        assumed_roi = st.number_input(
            "Assumed Revenue Impact per £1",
            min_value=0.0,
            max_value=10.0,
            value=3.0,
            step=0.5,
            help="How much revenue increases per additional £1 of marketing"
        )

    if scenario_change != 0:
        new_marketing = annual_marketing * (1 + scenario_change / 100)
        marketing_delta = new_marketing - annual_marketing

        # Estimate revenue impact
        if scenario_change > 0:
            # Increasing spend
            revenue_impact = marketing_delta * assumed_roi
        else:
            # Decreasing spend (assume higher ROI loss on cuts)
            revenue_impact = marketing_delta * assumed_roi * 1.2  # 20% penalty

        new_revenue = total_revenue + revenue_impact

        with col3:
            st.metric(
                "New Total Revenue",
                format_currency(new_revenue),
                format_currency(revenue_impact)
            )

        # Show scenario summary
        st.markdown("#### 📊 Scenario Summary")

        scenario_df = pd.DataFrame({
            'Metric': ['Marketing Budget', 'Total Revenue', 'Marketing % of Revenue'],
            'Current': [
                format_currency(annual_marketing),
                format_currency(total_revenue),
                f"{marketing_pct:.1f}%"
            ],
            'Scenario': [
                format_currency(new_marketing),
                format_currency(new_revenue),
                f"{(new_marketing / new_revenue * 100):.1f}%"
            ],
            'Change': [
                format_currency(marketing_delta),
                format_currency(revenue_impact),
                f"{((new_marketing / new_revenue) - (annual_marketing / total_revenue)) * 100:+.1f}pp"
            ]
        })

        st.dataframe(scenario_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Download marketing data
    st.markdown("### ⬇️ Export Marketing Data")

    # Build export dataframe
    export_data = []
    for territory, data_dict in marketing_data.items():
        for month, value in data_dict['budget'].items():
            export_data.append({
                'Territory': territory,
                'Channel': data_dict['channel'],
                'Month': month,
                'Marketing Spend': value
            })

    export_df = pd.DataFrame(export_data)

    csv = export_df.to_csv(index=False)

    st.download_button(
        label="📥 Download Marketing Data (CSV)",
        data=csv,
        file_name="marketing_budget_data.csv",
        mime="text/csv"
    )
