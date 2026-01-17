"""
Phase 1 Feature Enhancements for Budget Planning App
High-value features that enhance collaboration, analysis, and productivity
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from calculations import PLCalculator, format_currency


def render_comments_system(data):
    """
    Comments & Annotations System
    Allow users to add notes, flags, and comments to budget line items
    """
    st.markdown('<p class="main-header">📝 Comments & Notes</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Collaborate and annotate your budget</p>', unsafe_allow_html=True)

    if not data:
        st.warning("Please upload a budget file first")
        return

    # Initialize comments in session state
    if 'budget_comments' not in st.session_state:
        st.session_state.budget_comments = []

    # Add new comment section
    st.markdown("### ➕ Add New Comment")

    col1, col2, col3 = st.columns(3)

    with col1:
        comment_category = st.selectbox(
            "Category",
            ["Revenue", "Costs", "Overheads", "Assumptions", "General"]
        )

    with col2:
        comment_territory = st.selectbox(
            "Territory (if applicable)",
            ["All", "UK", "ES", "DE", "IT", "FR", "RO", "PL", "CZ", "HU", "SK"]
        )

    with col3:
        comment_status = st.selectbox(
            "Status",
            ["📌 For Review", "✅ Approved", "⚠️ Flagged", "💬 Discussion", "✓ Resolved"]
        )

    comment_text = st.text_area(
        "Comment",
        placeholder="Add your comment or question here...",
        height=100
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 Save Comment", type="primary"):
            if comment_text.strip():
                new_comment = {
                    'id': len(st.session_state.budget_comments) + 1,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'category': comment_category,
                    'territory': comment_territory,
                    'status': comment_status,
                    'text': comment_text,
                    'author': 'Current User'  # In production, use actual user auth
                }
                st.session_state.budget_comments.append(new_comment)
                st.success("✅ Comment added!")
                st.rerun()
            else:
                st.error("Please enter a comment")

    st.markdown("---")

    # Display existing comments
    st.markdown("### 💬 All Comments")

    if not st.session_state.budget_comments:
        st.info("No comments yet. Add your first comment above!")
    else:
        # Filter options
        col1, col2, col3 = st.columns(3)

        with col1:
            filter_category = st.multiselect(
                "Filter by Category",
                ["Revenue", "Costs", "Overheads", "Assumptions", "General"],
                default=["Revenue", "Costs", "Overheads", "Assumptions", "General"]
            )

        with col2:
            filter_status = st.multiselect(
                "Filter by Status",
                ["📌 For Review", "✅ Approved", "⚠️ Flagged", "💬 Discussion", "✓ Resolved"],
                default=["📌 For Review", "✅ Approved", "⚠️ Flagged", "💬 Discussion"]
            )

        with col3:
            show_resolved = st.checkbox("Show Resolved", value=False)

        # Filter comments
        filtered_comments = [
            c for c in st.session_state.budget_comments
            if c['category'] in filter_category
            and c['status'] in filter_status
            and (show_resolved or c['status'] != '✓ Resolved')
        ]

        # Display comments
        for comment in reversed(filtered_comments):  # Most recent first
            with st.expander(
                f"{comment['status']} | {comment['category']} - {comment['territory']} | {comment['timestamp']}",
                expanded=False
            ):
                st.markdown(f"**Comment:** {comment['text']}")
                st.markdown(f"*By {comment['author']} on {comment['timestamp']}*")

                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button("🗑️ Delete", key=f"del_{comment['id']}"):
                        st.session_state.budget_comments = [
                            c for c in st.session_state.budget_comments if c['id'] != comment['id']
                        ]
                        st.rerun()

        # Summary stats
        st.markdown("---")
        st.markdown("### 📊 Comment Summary")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total = len(st.session_state.budget_comments)
            st.metric("Total Comments", total)

        with col2:
            for_review = len([c for c in st.session_state.budget_comments if c['status'] == '📌 For Review'])
            st.metric("For Review", for_review)

        with col3:
            flagged = len([c for c in st.session_state.budget_comments if c['status'] == '⚠️ Flagged'])
            st.metric("Flagged", flagged)

        with col4:
            resolved = len([c for c in st.session_state.budget_comments if c['status'] == '✓ Resolved'])
            st.metric("Resolved", resolved)


def render_assumptions_register(data):
    """
    Assumptions Register
    Document and track key assumptions behind the budget
    """
    st.markdown('<p class="main-header">📋 Assumptions Register</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Document the "why" behind your numbers</p>', unsafe_allow_html=True)

    if not data:
        st.warning("Please upload a budget file first")
        return

    # Initialize assumptions in session state
    if 'budget_assumptions' not in st.session_state:
        st.session_state.budget_assumptions = [
            {
                'id': 1,
                'category': 'Revenue',
                'assumption': 'DTC Growth Rate',
                'value': '20% YoY',
                'rationale': 'Based on 2025 Q4 trend (+18%) plus new product launch impact (+5%) minus market headwinds (-3%)',
                'source': '2025 actuals + Marketing forecast',
                'confidence': 'Medium',
                'last_updated': '2026-01-15'
            },
            {
                'id': 2,
                'category': 'Costs',
                'assumption': 'CoGS Rate - DTC',
                'value': '24%',
                'rationale': 'Historical average 23-25%, supply chain improvements offset by inflation',
                'source': 'Finance analysis of 2025 data',
                'confidence': 'High',
                'last_updated': '2026-01-10'
            }
        ]

    # Add new assumption
    st.markdown("### ➕ Add New Assumption")

    col1, col2 = st.columns(2)

    with col1:
        assump_category = st.selectbox(
            "Category",
            ["Revenue", "Costs", "Overheads", "Market", "Operations", "Other"],
            key="new_assump_category"
        )

        assump_name = st.text_input(
            "Assumption Name",
            placeholder="e.g., B2B Growth Rate",
            key="new_assump_name"
        )

        assump_value = st.text_input(
            "Value",
            placeholder="e.g., 15% YoY",
            key="new_assump_value"
        )

    with col2:
        assump_confidence = st.selectbox(
            "Confidence Level",
            ["High", "Medium", "Low"],
            key="new_assump_confidence"
        )

        assump_source = st.text_input(
            "Data Source",
            placeholder="e.g., Customer contracts, Historical data",
            key="new_assump_source"
        )

    assump_rationale = st.text_area(
        "Rationale & Supporting Evidence",
        placeholder="Explain the reasoning and evidence behind this assumption...",
        height=100,
        key="new_assump_rationale"
    )

    if st.button("💾 Save Assumption", type="primary"):
        if assump_name.strip() and assump_value.strip():
            new_assumption = {
                'id': len(st.session_state.budget_assumptions) + 1,
                'category': assump_category,
                'assumption': assump_name,
                'value': assump_value,
                'rationale': assump_rationale,
                'source': assump_source,
                'confidence': assump_confidence,
                'last_updated': datetime.now().strftime('%Y-%m-%d')
            }
            st.session_state.budget_assumptions.append(new_assumption)
            st.success("✅ Assumption added!")
            st.rerun()
        else:
            st.error("Please enter assumption name and value")

    st.markdown("---")

    # Display assumptions
    st.markdown("### 📚 Assumption Library")

    # Filter by category and confidence
    col1, col2 = st.columns(2)

    with col1:
        filter_cat = st.multiselect(
            "Filter by Category",
            ["Revenue", "Costs", "Overheads", "Market", "Operations", "Other"],
            default=["Revenue", "Costs", "Overheads", "Market", "Operations", "Other"]
        )

    with col2:
        filter_conf = st.multiselect(
            "Filter by Confidence",
            ["High", "Medium", "Low"],
            default=["High", "Medium", "Low"]
        )

    filtered_assumptions = [
        a for a in st.session_state.budget_assumptions
        if a['category'] in filter_cat and a['confidence'] in filter_conf
    ]

    # Display as expandable cards
    for assump in filtered_assumptions:
        confidence_color = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}[assump['confidence']]

        with st.expander(
            f"{confidence_color} {assump['category']} | {assump['assumption']}: **{assump['value']}**",
            expanded=False
        ):
            st.markdown(f"**Rationale:** {assump['rationale']}")
            st.markdown(f"**Source:** {assump['source']}")
            st.markdown(f"**Confidence:** {assump['confidence']}")
            st.markdown(f"**Last Updated:** {assump['last_updated']}")

            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("🗑️ Delete", key=f"del_assump_{assump['id']}"):
                    st.session_state.budget_assumptions = [
                        a for a in st.session_state.budget_assumptions if a['id'] != assump['id']
                    ]
                    st.rerun()

    # Summary
    st.markdown("---")
    st.markdown("### 📊 Assumption Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        total_assumptions = len(st.session_state.budget_assumptions)
        st.metric("Total Assumptions", total_assumptions)

    with col2:
        high_confidence = len([a for a in st.session_state.budget_assumptions if a['confidence'] == 'High'])
        st.metric("High Confidence", high_confidence)

    with col3:
        low_confidence = len([a for a in st.session_state.budget_assumptions if a['confidence'] == 'Low'])
        st.metric("Low Confidence", low_confidence)
        if low_confidence > 0:
            st.warning(f"⚠️ {low_confidence} assumption(s) need review")


def render_data_quality_dashboard(data):
    """
    Data Quality Dashboard
    Check for missing data, anomalies, and validation issues
    """
    st.markdown('<p class="main-header">🛡️ Data Quality Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Ensure data integrity and completeness</p>', unsafe_allow_html=True)

    if not data:
        st.warning("Please upload a budget file first")
        return

    calc = PLCalculator(data)

    # Overall data quality score
    issues = []
    warnings = []

    st.markdown("### 📊 Data Quality Score")

    # Check 1: Data completeness
    st.markdown("#### 1. Data Completeness")

    territories = ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK', 'Other EU']
    missing_dtc = []

    for territory in territories:
        if territory not in data.get('dtc', {}):
            missing_dtc.append(territory)

    if missing_dtc:
        st.warning(f"⚠️ Missing DTC data for: {', '.join(missing_dtc)}")
        warnings.append(f"Missing DTC territories: {len(missing_dtc)}")
    else:
        st.success("✅ All DTC territories have data")

    # Check B2B data
    if data.get('b2b') is not None and not data['b2b'].empty:
        date_cols = [c for c in data['b2b'].columns if c.startswith('202')]
        if len(date_cols) < 12:
            st.warning(f"⚠️ B2B data has only {len(date_cols)} months (expected 12)")
            warnings.append(f"Incomplete B2B time series")
        else:
            st.success(f"✅ B2B data complete ({len(date_cols)} months)")
    else:
        st.error("❌ No B2B data loaded")
        issues.append("Missing B2B data")

    # Check 2: Revenue validation
    st.markdown("#### 2. Revenue Validation")

    b2b_total = sum(calc.calculate_b2b_revenue().values())
    dtc_territories = ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK', 'Other EU']
    dtc_total = sum(sum(calc.calculate_dtc_revenue(t).values()) for t in dtc_territories if t in data.get('dtc', {}))
    mp_total = sum(calc.calculate_total_marketplace_revenue().values())
    total_revenue = b2b_total + dtc_total + mp_total

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("B2B Revenue", f"£{b2b_total/1e6:.1f}M")
        if b2b_total == 0:
            st.error("❌ B2B revenue is zero")
            issues.append("Zero B2B revenue")

    with col2:
        st.metric("DTC Revenue", f"£{dtc_total/1e6:.1f}M")
        if dtc_total == 0:
            st.error("❌ DTC revenue is zero")
            issues.append("Zero DTC revenue")

    with col3:
        st.metric("Total Revenue", f"£{total_revenue/1e6:.1f}M")
        if total_revenue < 10e6:
            st.warning("⚠️ Total revenue seems low (<£10M)")
            warnings.append("Low total revenue")

    # Check 3: Anomaly detection
    st.markdown("#### 3. Anomaly Detection")

    anomalies_found = False

    # Check for extreme month-over-month growth
    for territory in dtc_territories:
        if territory in data.get('dtc', {}):
            territory_rev = calc.calculate_dtc_revenue(territory)
            values = list(territory_rev.values())

            if len(values) > 1:
                for i in range(1, len(values)):
                    if values[i-1] > 0:
                        growth = ((values[i] - values[i-1]) / values[i-1]) * 100
                        if abs(growth) > 200:
                            st.warning(f"⚠️ {territory} DTC: {growth:+.0f}% MoM growth detected")
                            warnings.append(f"{territory} extreme growth")
                            anomalies_found = True

    # Check for negative margins
    if data.get('cogs_rates'):
        for channel, rate in data['cogs_rates'].items():
            if rate < 0 or rate > 1:
                st.warning(f"⚠️ {channel} CoGS rate ({rate:.1%}) seems unusual")
                warnings.append(f"Unusual {channel} CoGS rate")
                anomalies_found = True

    if not anomalies_found:
        st.success("✅ No major anomalies detected")

    # Check 4: Reconciliation
    st.markdown("#### 4. Reconciliation Checks")

    # Check if combined P&L matches sum of components
    combined_pl = calc.calculate_combined_pl()
    if ('Revenue', 'Total Revenue') in combined_pl.index:
        date_cols = [c for c in combined_pl.columns if c.startswith('202')]
        pl_revenue = combined_pl.loc[('Revenue', 'Total Revenue'), date_cols].sum()

        diff = abs(pl_revenue - total_revenue)
        if diff < 100:
            st.success(f"✅ Revenue reconciles: P&L (£{pl_revenue:,.0f}) matches sum of channels")
        else:
            st.error(f"❌ Revenue mismatch: P&L shows £{pl_revenue:,.0f} but channels sum to £{total_revenue:,.0f}")
            issues.append(f"Revenue reconciliation error: £{diff:,.0f} difference")

    # Final score
    st.markdown("---")
    st.markdown("### 🎯 Overall Data Quality")

    total_checks = 10
    passed_checks = total_checks - len(issues) - (len(warnings) * 0.5)
    score = (passed_checks / total_checks) * 100

    col1, col2, col3 = st.columns(3)

    with col1:
        score_color = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
        st.metric("Quality Score", f"{score_color} {score:.0f}%")

    with col2:
        st.metric("Critical Issues", len(issues), delta_color="inverse")

    with col3:
        st.metric("Warnings", len(warnings), delta_color="inverse")

    if score >= 80:
        st.success("✅ Data quality is good! Your budget data is ready for analysis.")
    elif score >= 60:
        st.warning("⚠️ Data quality is acceptable but has some issues. Review warnings above.")
    else:
        st.error("❌ Data quality needs improvement. Please address critical issues above.")


def render_waterfall_analysis(data):
    """
    Waterfall Analysis
    Visual breakdown showing how you get from revenue to EBITDA
    """
    st.markdown('<p class="main-header">📊 Waterfall Analysis</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Visual P&L breakdown: Revenue to EBITDA</p>', unsafe_allow_html=True)

    if not data:
        st.warning("Please upload a budget file first")
        return

    calc = PLCalculator(data)

    # Time period selector
    col1, col2 = st.columns(2)

    with col1:
        analysis_type = st.selectbox(
            "Analysis Type",
            ["Annual Total", "Monthly Breakdown", "Quarterly View"]
        )

    with col2:
        if analysis_type == "Monthly Breakdown":
            selected_month = st.selectbox(
                "Select Month",
                data.get('dates', [])
            )

    st.markdown("---")

    # Calculate P&L
    combined_pl = calc.calculate_combined_pl()

    if combined_pl.empty:
        st.error("Unable to calculate P&L")
        return

    date_cols = [c for c in combined_pl.columns if c.startswith('202')]

    if analysis_type == "Annual Total":
        # Annual waterfall
        try:
            revenue = combined_pl.loc[('Revenue', 'Total Revenue'), date_cols].sum()
            cogs = combined_pl.loc[('CoGS', 'Total CoGS'), date_cols].sum()
            fulfilment = combined_pl.loc[('Fulfilment', 'Total Fulfilment'), date_cols].sum()
            overheads = combined_pl.loc[('Overheads', 'Overheads'), date_cols].sum()
            ebitda = combined_pl.loc[('EBITDA', 'EBITDA'), date_cols].sum()

            # Create waterfall chart
            fig = go.Figure(go.Waterfall(
                name="P&L Waterfall",
                orientation="v",
                measure=["absolute", "relative", "relative", "relative", "total"],
                x=["Revenue", "CoGS", "Fulfilment", "Overheads", "EBITDA"],
                y=[revenue, cogs, fulfilment, overheads, ebitda],
                text=[
                    format_currency(revenue),
                    format_currency(cogs),
                    format_currency(fulfilment),
                    format_currency(overheads),
                    format_currency(ebitda)
                ],
                textposition="outside",
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                decreasing={"marker": {"color": "#EF553B"}},
                increasing={"marker": {"color": "#00CC96"}},
                totals={"marker": {"color": "#636EFA"}}
            ))

            fig.update_layout(
                title="Annual P&L Waterfall: Revenue to EBITDA",
                showlegend=False,
                height=500,
                yaxis_title="Amount (£)"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Metrics
            st.markdown("### 📊 Key Metrics")

            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.metric("Revenue", format_currency(revenue))

            with col2:
                cm1 = revenue + cogs
                cm1_pct = (cm1 / revenue * 100) if revenue > 0 else 0
                st.metric("CM1", format_currency(cm1), f"{cm1_pct:.1f}%")

            with col3:
                cm2 = cm1 + fulfilment
                cm2_pct = (cm2 / revenue * 100) if revenue > 0 else 0
                st.metric("CM2", format_currency(cm2), f"{cm2_pct:.1f}%")

            with col4:
                ebitda_pct = (ebitda / revenue * 100) if revenue > 0 else 0
                st.metric("EBITDA", format_currency(ebitda), f"{ebitda_pct:.1f}%")

            with col5:
                cogs_pct = abs(cogs / revenue * 100) if revenue > 0 else 0
                st.metric("CoGS %", f"{cogs_pct:.1f}%")

        except KeyError as e:
            st.error(f"Missing P&L data: {e}")

    elif analysis_type == "Monthly Breakdown":
        # Monthly waterfall for selected month
        try:
            month = selected_month

            revenue = combined_pl.loc[('Revenue', 'Total Revenue'), month]
            cogs = combined_pl.loc[('CoGS', 'Total CoGS'), month]
            fulfilment = combined_pl.loc[('Fulfilment', 'Total Fulfilment'), month]
            overheads = combined_pl.loc[('Overheads', 'Overheads'), month]
            ebitda = combined_pl.loc[('EBITDA', 'EBITDA'), month]

            # Create waterfall chart
            fig = go.Figure(go.Waterfall(
                name="P&L Waterfall",
                orientation="v",
                measure=["absolute", "relative", "relative", "relative", "total"],
                x=["Revenue", "CoGS", "Fulfilment", "Overheads", "EBITDA"],
                y=[revenue, cogs, fulfilment, overheads, ebitda],
                text=[
                    format_currency(revenue),
                    format_currency(cogs),
                    format_currency(fulfilment),
                    format_currency(overheads),
                    format_currency(ebitda)
                ],
                textposition="outside",
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                decreasing={"marker": {"color": "#EF553B"}},
                increasing={"marker": {"color": "#00CC96"}},
                totals={"marker": {"color": "#636EFA"}}
            ))

            fig.update_layout(
                title=f"P&L Waterfall for {month}",
                showlegend=False,
                height=500,
                yaxis_title="Amount (£)"
            )

            st.plotly_chart(fig, use_container_width=True)

        except KeyError as e:
            st.error(f"Missing data for {month}: {e}")

    # Channel contribution breakdown
    st.markdown("---")
    st.markdown("### 📈 Revenue Contribution by Channel")

    b2b_total = sum(calc.calculate_b2b_revenue().values())
    dtc_territories = ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK', 'Other EU']
    dtc_total = sum(sum(calc.calculate_dtc_revenue(t).values()) for t in dtc_territories if t in data.get('dtc', {}))
    mp_total = sum(calc.calculate_total_marketplace_revenue().values())

    channel_data = pd.DataFrame({
        'Channel': ['B2B', 'DTC', 'Marketplace'],
        'Revenue': [b2b_total, dtc_total, mp_total]
    })

    fig = px.bar(
        channel_data,
        x='Channel',
        y='Revenue',
        text=channel_data['Revenue'].apply(lambda x: format_currency(x)),
        color='Channel',
        color_discrete_map={'B2B': '#636EFA', 'DTC': '#00CC96', 'Marketplace': '#FFA15A'}
    )

    fig.update_layout(
        title="Annual Revenue by Channel",
        yaxis_title="Revenue (£)",
        showlegend=False,
        height=400
    )

    fig.update_traces(textposition='outside')

    st.plotly_chart(fig, use_container_width=True)
