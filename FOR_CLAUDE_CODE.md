# Budget Planning App - Context for Claude Code

**Last Updated**: 2026-01-17 | **Version**: 1.0.1 | **Status**: Production

---

## 📋 Quick Reference

### Current State
- **Deployment**: Streamlit Cloud (auto-deploys from GitHub main branch)
- **Repository**: https://github.com/Rdwburns/budget-planning-app
- **Excel Source**: `Copy of Budget FY26-27 Base.xlsx` (FY27 = 2026-02 to 2027-01)
- **Expected Revenue**: £23,399,235 (B2B: £7.6M, DTC: £12.5M, Marketplace: £3.3M)

### Critical Files
```
app.py                    # Main Streamlit app (2746 lines)
calculations.py           # P&L calculation engine with territory mapping
data_loader.py           # Excel data loading and validation
features_phase1.py       # Phase 1 collaboration features
SUGGESTED_FEATURES.md    # 27 prioritized feature ideas
PHASE1_SUMMARY.md        # Phase 1 implementation details
```

---

## 🐛 Recently Fixed Critical Issues

### Issue 1: B2B Territory Filtering Bug
**Problem**: P&L View showed £17.6M instead of £23.4M due to territory code mismatch
**Root Cause**: `calculate_b2b_revenue(territory='UK')` filtered by 'UK' but B2B data has 'United Kingdom'
**Fix**: Added `territory_to_country` mapping dictionary in `calculations.py:36-47`
```python
self.territory_to_country = {
    'UK': 'United Kingdom',
    'ES': 'Spain',
    # ... etc
}
```
**Location**: [calculations.py:35-67](calculations.py#L35-L67)
**Commit**: b727f8f

### Issue 2: Missing Territories in Combined P&L
**Problem**: Combined P&L missing 'Other EU' and marketplace-only territories (FR, DE, PL, US, AU, ROW)
**Fix**: Expanded territory list from 8 to 14 territories
**Location**: [calculations.py:224](calculations.py#L224)
**Commit**: b727f8f

### Issue 3: Scenario Sliders Not Working
**Problem**: Scenario adjustments not applied to B2B/Marketplace in Detailed P&L
**Fix**: Changed scenario keys to `'b2b_growth'` and `'mp_growth'` to match UI
**Location**: [calculations.py:64-67, 128-130](calculations.py#L64-L67)
**Commit**: b727f8f

---

## ✨ Phase 1 Features Implemented

### 1. Comments & Notes System (📝)
**Location**: `features_phase1.py::render_comments_system()`
**Purpose**: Team collaboration on budget items
**Features**: Status flags, filtering, comment summary
**Session State**: `st.session_state.budget_comments`

### 2. Assumptions Register (📋)
**Location**: `features_phase1.py::render_assumptions_register()`
**Purpose**: Document the "why" behind numbers
**Features**: Confidence levels, rationale, source tracking
**Session State**: `st.session_state.budget_assumptions`

### 3. Data Quality Dashboard (🛡️)
**Location**: `features_phase1.py::render_data_quality_dashboard()`
**Purpose**: Validate data integrity
**Checks**: Completeness, anomalies, reconciliation, quality score

### 4. Waterfall Analysis (💧)
**Location**: `features_phase1.py::render_waterfall_analysis()`
**Purpose**: Visual P&L breakdown
**Features**: Annual/monthly views, Plotly waterfall charts, channel breakdown

---

## 🏗️ Architecture Overview

### Data Flow
```
Excel File → data_loader.py → Session State → calculations.py → Streamlit UI
                                    ↓
                            features_phase1.py
```

### Key Calculation Methods
- `calculate_b2b_revenue(territory=None, country_group=None)` - B2B revenue with territory mapping
- `calculate_dtc_revenue(territory)` - DTC revenue for one territory
- `calculate_marketplace_revenue(territory)` - Amazon revenue for one territory
- `calculate_territory_pl(territory)` - Full P&L for one territory
- `calculate_combined_pl()` - Aggregated P&L across all 14 territories

### Territory Codes
**DTC Territories** (8): UK, ES, IT, RO, CZ, HU, SK, Other EU
**Marketplace-Only** (6): FR, DE, PL, US, AU, ROW
**Total**: 14 territories

### Session State Schema
```python
st.session_state = {
    'data': dict,                    # Loaded Excel data
    'file_loaded': bool,
    'loaded_file_id': str,
    'budget_versions': list,         # Version control
    'budget_comments': list,         # Phase 1: Comments
    'budget_assumptions': list,      # Phase 1: Assumptions
    # ... more state ...
}
```

---

## 🎯 Next Phase Priorities (SUGGESTED_FEATURES.md)

### Phase 2: Enhanced Analysis (High Priority)
1. **Enhanced Variance Analysis** - Volume/price/mix breakdown of budget vs actuals
2. **Key Driver Analysis** - Tornado charts showing what drives EBITDA
3. **Bulk Operations** - Copy months, smart fill, distribute totals

### Phase 3: Workflow & Automation
4. **Approval Workflow** - Multi-level sign-off with audit trail
5. **Smart Alerts** - Threshold notifications, proactive issue detection
6. **Templates** - Save and reuse scenario configurations

### Phase 4: Advanced Analytics
7. **Trend Forecasting** - ML-based revenue projection
8. **Cash Flow Projection** - Payment terms and working capital
9. **Goal Seek** - Work backwards from EBITDA targets

### Phase 5: Integration & Polish
10. **Database Persistence** - SQLite/PostgreSQL for data storage
11. **Audit Trail** - Complete edit history
12. **Excel Round-Trip** - Export, edit, re-import

**Full details**: See SUGGESTED_FEATURES.md for all 27 features with effort estimates

---

## ⚠️ Known Gotchas

### 1. Streamlit Cloud Deployment Lag
**Issue**: Code pushed to GitHub may take 2-5 minutes to deploy
**Solution**: Look for version badge in sidebar to confirm deployment
**Badge Location**: [app.py:92-98](app.py#L92-L98)

### 2. Dashboard vs P&L Calculation Paths
**Dashboard**: Uses `calculate_b2b_revenue()` with NO territory filter → Gets all revenue
**P&L View**: Uses `calculate_combined_pl()` → Loops through territories → Needs territory mapping
**Implication**: Dashboard can work while P&L View fails if territory mapping is broken

### 3. Session State Not Persisted
**Current**: All data in `st.session_state` - lost on app restart
**Why**: Simplicity for MVP, avoids database complexity
**Future**: Phase 5 will add database for persistence

### 4. FY27 Date Range
**Excel Model**: FY27 = 2026-02 to 2027-01 (12 months)
**Filter Logic**: `data_loader.py::filter_fy27_columns()`
**Important**: All date filtering uses this range

### 5. Territory Name Mapping Required
**B2B Data**: Uses full country names ('United Kingdom', 'Spain')
**Amazon Data**: Mix of codes ('UK') and names ('Spain', 'United States')
**DTC Data**: Uses territory codes ('UK', 'ES')
**Solution**: Mapping dictionaries in `calculations.py` and `calculate_marketplace_revenue()`

---

## 🔧 Development Workflow

### Testing Locally
```bash
# Streamlit not installed locally - test on Streamlit Cloud
# Changes auto-deploy on push to main branch
```

### Deployment Process
1. Make changes to local files
2. Test logic without running app (use Python scripts)
3. Commit with detailed message
4. Push to GitHub main branch
5. Wait 2-5 minutes for Streamlit Cloud to deploy
6. Hard refresh browser (Cmd+Shift+R) to see changes
7. Check version badge in sidebar to confirm deployment

### Git Commit Best Practices
- Use descriptive commit messages with "what" and "why"
- Include Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
- Reference issue numbers or feature names
- Group related changes in single commit

---

## 📊 Data Validation Checklist

When adding new features that touch calculations:

1. **Revenue Totals Must Match**
   - Dashboard total = P&L View total = £23.4M
   - B2B = £7.6M, DTC = £12.5M, Marketplace = £3.3M

2. **Territory Filtering**
   - Always use territory mapping for B2B data
   - Check if Amazon data uses codes or full names
   - Verify DTC territories exist before calculating

3. **Date Range**
   - Filter to FY27 period (2026-02 to 2027-01)
   - Use `filter_fy27_columns()` from data_loader

4. **Scenario Adjustments**
   - Match keys between UI sliders and calculation methods
   - Apply to correct revenue streams

5. **P&L Reconciliation**
   - Revenue - CoGS - Fulfilment - Overheads = EBITDA
   - All channels must sum to total

---

## 🎨 UI/UX Patterns

### Navigation Structure
```
Sidebar (render_sidebar)
├── Version Badge
├── Navigation Menu (14 pages)
│   ├── Dashboard
│   ├── Revenue Inputs
│   ├── B2B Management
│   ├── Cost Management
│   ├── Scenario Planning
│   ├── P&L View
│   ├── Budget vs Actuals
│   ├── Version Control
│   ├── Sensitivity Analysis
│   ├── Comments & Notes (Phase 1)
│   ├── Assumptions (Phase 1)
│   ├── Data Quality (Phase 1)
│   ├── Waterfall Analysis (Phase 1)
│   └── Export
├── File Upload
└── Version Control Quick Actions
```

### Page Rendering Pattern
```python
def render_page_name(data):
    st.markdown('<p class="main-header">📊 Title</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Subtitle</p>', unsafe_allow_html=True)

    if not data:
        st.warning("Please upload a budget file first")
        return

    # Feature implementation
    calc = PLCalculator(data)
    # ... calculations ...

    # Display results
    st.metric("KPI Name", value)
    st.plotly_chart(fig)
```

### Common UI Components
- `st.metric()` - KPI cards
- `st.plotly_chart()` - Interactive charts
- `st.expander()` - Collapsible sections
- `st.columns()` - Side-by-side layout
- `st.selectbox()`, `st.multiselect()` - Filters
- `st.button(type="primary")` - Primary actions

---

## 🐞 Debugging Tips

### Revenue Calculation Issues
1. Check Dashboard first - does it show correct total?
2. If Dashboard correct but P&L wrong → territory mapping issue
3. Check `calculate_b2b_revenue()` for territory filtering
4. Verify territory list in `calculate_combined_pl()`

### Deployment Issues
1. Check version badge - is it the expected version?
2. Hard refresh browser (Cmd+Shift+R)
3. Check Streamlit Cloud logs for build errors
4. Verify commit was pushed to main branch

### Data Loading Issues
1. Check `data['validation_warnings']` for warnings
2. Verify Excel file has all expected sheets
3. Check date column format (YYYY-MM)
4. Ensure FY27 date range (2026-02 to 2027-01)

### Session State Issues
1. Session state lost on page change? → Use `st.session_state` not local vars
2. Data not persisting? → Expected - no database yet
3. State growing too large? → Clean up old versions

---

## 📚 Feature Implementation Guide

### Adding a New Feature

1. **Plan**
   - Review SUGGESTED_FEATURES.md for specs
   - Identify data dependencies
   - Design session state schema

2. **Implement**
   - Add rendering function to `features_phase1.py` (or new module)
   - Import in `app.py`
   - Add to navigation menu
   - Add page routing in main()

3. **Test**
   - Test calculation logic separately
   - Push to GitHub
   - Wait for deployment
   - Verify in browser

4. **Document**
   - Update PHASE1_SUMMARY.md
   - Add to FOR_CLAUDE_CODE.md
   - Update SUGGESTED_FEATURES.md status

### Code Style Guidelines
- Use descriptive variable names
- Add docstrings to all functions
- Format currency with `format_currency()`
- Use session state for all persistent data
- Handle empty data gracefully (`if not data:`)
- Add type hints where helpful
- Keep functions focused (single responsibility)

---

## 🎯 Success Criteria

### For New Features
- ✅ Works with uploaded Excel file
- ✅ Handles missing data gracefully
- ✅ Uses session state for persistence
- ✅ Follows existing UI patterns
- ✅ Includes clear error messages
- ✅ Documented in FOR_CLAUDE_CODE.md
- ✅ Tested on deployed app

### For Bug Fixes
- ✅ Root cause identified and documented
- ✅ Fix verified locally (if possible)
- ✅ Revenue totals still match (£23.4M)
- ✅ No regression in other features
- ✅ Committed with detailed message

---

## 📞 Quick Reference Commands

### Git Commands
```bash
git status                          # Check what's changed
git add -A                          # Stage all changes
git commit -m "message"            # Commit with message
git push origin main               # Deploy to production
git log --oneline -5               # Recent commits
```

### File Locations
```bash
/Users/roryarmitage-burns/budget-planning-app/
├── app.py                         # Main app
├── calculations.py                # Calculation engine
├── data_loader.py                # Data loading
├── features_phase1.py            # Phase 1 features
├── Copy of Budget FY26-27 Base.xlsx  # Source data
├── SUGGESTED_FEATURES.md         # Feature roadmap
├── PHASE1_SUMMARY.md            # Phase 1 details
└── FOR_CLAUDE_CODE.md           # This file
```

---

## 🚨 Emergency Fixes

### If Revenue Totals Are Wrong
1. Check `calculate_combined_pl()` territory list
2. Verify `territory_to_country` mapping is applied
3. Confirm all 14 territories included
4. Test with `verify_fixes.py` (if pandas installed)

### If App Won't Load
1. Check Streamlit Cloud build logs
2. Verify no import errors
3. Check `requirements.txt` has all dependencies
4. Roll back to previous commit if needed

### If Data Won't Upload
1. Check file format (must be .xlsx)
2. Verify sheet names match expected (B2B, Overheads, etc.)
3. Check date columns are formatted correctly
4. Review validation warnings in sidebar

---

**For Questions**: Review SUGGESTED_FEATURES.md and PHASE1_SUMMARY.md first
**For Bugs**: Document in comments and reference this file
**For New Features**: Follow Feature Implementation Guide above

**Last Updated**: 2026-01-17 by Claude Sonnet 4.5
