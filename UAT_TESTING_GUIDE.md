# Budget Planning App - UAT Testing Guide & Checklist

**Version**: 1.0.1
**Test Date**: _____________
**Tester Name**: _____________
**Environment**: Production (Streamlit Cloud)

---

## 📋 Pre-Test Setup

### ☑ Prerequisites Checklist

- [ ] Access to Streamlit Cloud app URL
- [ ] Budget Excel file ready (`Copy of Budget FY26-27 Base.xlsx`)
- [ ] Browser: Chrome, Safari, or Firefox (latest version)
- [ ] Screen resolution: Minimum 1280x720
- [ ] Stable internet connection
- [ ] Notepad for recording issues/feedback

---

## 🎯 Test Objectives

1. **Functionality**: All features work as expected
2. **Accuracy**: Calculations match Excel source
3. **Usability**: Interface is intuitive and easy to use
4. **Performance**: App loads and responds quickly
5. **Data Quality**: No errors in data loading or processing

---

## 📊 Test Scenarios

### TEST 1: App Access & Initial Load

**Objective**: Verify app loads correctly and shows version badge

**Steps**:
1. Open browser and navigate to app URL
2. Wait for app to load (should take <10 seconds)
3. Check sidebar for version badge

**Expected Results**:
- [ ] App loads without errors
- [ ] Sidebar shows "✨ Version 1.0.1 - P&L Fixes Deployed" badge
- [ ] Navigation menu shows all 15 pages
- [ ] File upload area visible in sidebar

**Pass/Fail**: ______
**Notes**: _________________________________

---

### TEST 2: File Upload

**Objective**: Upload budget Excel file successfully

**Steps**:
1. Click "Upload Budget Excel" in sidebar
2. Select `Copy of Budget FY26-27 Base.xlsx`
3. Wait for "Loading data..." spinner
4. Check for "✅ Data loaded" success message

**Expected Results**:
- [ ] File uploads without errors
- [ ] Success message appears
- [ ] No validation warnings (or minor warnings only)
- [ ] Dashboard page loads with data

**Pass/Fail**: ______
**Notes**: _________________________________

---

### TEST 3: Dashboard - Revenue Totals

**Objective**: Verify dashboard shows correct revenue totals

**Steps**:
1. Navigate to "📊 Dashboard" (should be default)
2. Check KPI cards at top
3. Verify channel breakdown table

**Expected Results**:
- [ ] Total Revenue: £23.4M (±£100K)
- [ ] B2B Revenue: £7.6M (32.3%)
- [ ] DTC Revenue: £12.5M (53.5%)
- [ ] Marketplace Revenue: £3.3M (14.1%)
- [ ] Percentages sum to ~100%
- [ ] Charts display correctly

**Actual Values**:
- Total Revenue: £__________
- B2B: £__________
- DTC: £__________
- Marketplace: £__________

**Pass/Fail**: ______
**Notes**: _________________________________

---

### TEST 4: P&L View - Combined P&L

**Objective**: Verify P&L View matches Dashboard totals

**Steps**:
1. Navigate to "📈 P&L View"
2. Ensure "Combined" view selected
3. Check Total Revenue row
4. Verify EBITDA calculation

**Expected Results**:
- [ ] Total Revenue: £23.4M (matches Dashboard)
- [ ] B2B Revenue: £7.6M
- [ ] DTC Revenue: £12.5M
- [ ] Marketplace Revenue: £3.3M
- [ ] Total CoGS: Negative value (costs)
- [ ] Total Fulfilment: Negative value
- [ ] Overheads: Non-zero negative value (includes marketing)
- [ ] EBITDA: Calculated value
- [ ] All rows display without errors

**Actual Total Revenue in P&L**: £__________

**Pass/Fail**: ______
**Notes**: _________________________________

---

### TEST 5: P&L View - Territory Breakdown

**Objective**: Verify territory-specific P&Ls calculate correctly

**Steps**:
1. In P&L View, select "By Territory"
2. Choose territory: UK
3. Review revenue breakdown
4. Repeat for 2-3 other territories (ES, IT, RO)

**Expected Results**:
- [ ] Each territory shows DTC, B2B, Marketplace revenue
- [ ] UK shows significant revenue (largest territory)
- [ ] Costs calculate for each territory
- [ ] EBITDA = CM2 + Overheads
- [ ] No error messages

**Pass/Fail**: ______
**Notes**: _________________________________

---

### TEST 6: Marketing Management

**Objective**: Verify marketing spend data and ROI calculations

**Steps**:
1. Navigate to "📣 Marketing"
2. Check Total Marketing Budget card
3. Review territory spend chart
4. Check ROI analysis section

**Expected Results**:
- [ ] Total Marketing Budget shows non-zero value
- [ ] Marketing % of revenue displayed
- [ ] Territory breakdown chart shows multiple territories
- [ ] ROI calculation shows "£X per £1 marketing"
- [ ] Monthly trend chart displays
- [ ] Best ROI territory highlighted

**Actual Marketing Budget**: £__________
**Marketing % of Revenue**: ______%

**Pass/Fail**: ______
**Notes**: _________________________________

---

### TEST 7: Waterfall Analysis

**Objective**: Verify waterfall chart shows complete P&L breakdown

**Steps**:
1. Navigate to "💧 Waterfall Analysis"
2. Ensure "Annual Total" selected
3. Review waterfall chart
4. Check key metrics below chart

**Expected Results**:
- [ ] Waterfall shows: Revenue → CoGS → Fulfilment → Overheads → EBITDA
- [ ] Revenue bar: £23.4M (blue, tallest bar)
- [ ] CoGS: Negative (red bar)
- [ ] Fulfilment: Negative (red bar)
- [ ] **Overheads: Non-zero negative value (CRITICAL - was showing £0 before fix)**
- [ ] EBITDA: Positive or negative (blue bar)
- [ ] Metrics show CM1%, CM2%, EBITDA%
- [ ] Channel contribution chart displays below

**Actual Overheads in Waterfall**: £__________ (should be negative, non-zero)

**Pass/Fail**: ______
**Critical Issue if Overheads = £0**: YES / NO

**Notes**: _________________________________

---

### TEST 8: Data Quality Dashboard

**Objective**: Verify data validation and quality score

**Steps**:
1. Navigate to "🛡️ Data Quality"
2. Review each validation section
3. Check overall quality score

**Expected Results**:
- [ ] Data Completeness: ✅ All territories present
- [ ] Revenue Validation: All channels show non-zero values
- [ ] Anomaly Detection: No critical anomalies (warnings OK)
- [ ] Reconciliation: P&L matches channel sum (difference <£100)
- [ ] Overall Quality Score: ≥80% (green)
- [ ] No critical issues flagged

**Actual Quality Score**: ______%
**Critical Issues**: ______
**Warnings**: ______

**Pass/Fail**: ______
**Notes**: _________________________________

---

### TEST 9: Comments & Notes System

**Objective**: Test collaboration features

**Steps**:
1. Navigate to "📝 Comments & Notes"
2. Add new comment:
   - Category: Revenue
   - Territory: UK
   - Status: 📌 For Review
   - Text: "Test comment for UAT"
3. Save comment
4. Filter comments by status
5. Delete test comment

**Expected Results**:
- [ ] Comment form displays all fields
- [ ] Comment saves successfully
- [ ] Comment appears in list below
- [ ] Filtering works correctly
- [ ] Comment summary shows updated counts
- [ ] Delete button removes comment

**Pass/Fail**: ______
**Notes**: _________________________________

---

### TEST 10: Assumptions Register

**Objective**: Test assumption documentation feature

**Steps**:
1. Navigate to "📋 Assumptions"
2. Review pre-loaded examples
3. Add new assumption:
   - Category: Revenue
   - Name: "Test Growth Rate"
   - Value: "15%"
   - Confidence: Medium
   - Rationale: "UAT testing assumption"
4. Save and verify it appears
5. Delete test assumption

**Expected Results**:
- [ ] 2 pre-loaded examples visible
- [ ] New assumption saves successfully
- [ ] Confidence indicator shows correct color (🟡 for Medium)
- [ ] Filter by confidence works
- [ ] Summary metrics update
- [ ] Delete removes assumption

**Pass/Fail**: ______
**Notes**: _________________________________

---

### TEST 11: Scenario Planning

**Objective**: Verify scenario modeling works

**Steps**:
1. Navigate to "🎯 Scenario Planning"
2. Adjust DTC Revenue Growth slider to +10%
3. Click "Calculate Impact"
4. Review impact cards
5. Reset to 0% and recalculate

**Expected Results**:
- [ ] Sliders respond to input
- [ ] Calculate button triggers calculation
- [ ] Impact cards show revenue increase
- [ ] EBITDA impact calculates
- [ ] Detailed P&L updates with scenario
- [ ] Reset returns to baseline

**Pass/Fail**: ______
**Notes**: _________________________________

---

### TEST 12: Budget vs Actuals

**Objective**: Test comparison feature (if actuals data available)

**Steps**:
1. Navigate to "📉 Budget vs Actuals"
2. Check if actuals data loaded
3. If available, review variance analysis
4. Check variance charts

**Expected Results**:
- [ ] Page loads without errors
- [ ] If no actuals: Shows appropriate message
- [ ] If actuals present: Shows variance analysis
- [ ] Variance calculations look correct
- [ ] Charts display properly

**Pass/Fail**: ______
**Notes**: _________________________________

---

### TEST 13: Version Control

**Objective**: Test budget versioning feature

**Steps**:
1. Navigate to "📚 Version Control"
2. Save current version:
   - Name: "UAT Test Version"
   - Notes: "Testing version control"
3. Make a small change (adjust a scenario slider)
4. Compare with saved version
5. Restore saved version
6. Delete test version

**Expected Results**:
- [ ] Version saves successfully
- [ ] Saved versions list shows new version
- [ ] Compare shows differences
- [ ] Restore returns to saved state
- [ ] Delete removes version

**Pass/Fail**: ______
**Notes**: _________________________________

---

### TEST 14: Sensitivity Analysis

**Objective**: Test sensitivity analysis calculations

**Steps**:
1. Navigate to "📈 Sensitivity Analysis"
2. Select variable to analyze (e.g., DTC Growth)
3. Run sensitivity analysis
4. Review tornado chart and results table

**Expected Results**:
- [ ] Variable selection works
- [ ] Analysis runs without errors
- [ ] Tornado chart displays
- [ ] Results table shows impact ranges
- [ ] Insights make logical sense

**Pass/Fail**: ______
**Notes**: _________________________________

---

### TEST 15: Export Functionality

**Objective**: Test data export capabilities

**Steps**:
1. Navigate to "⬇️ Export"
2. Export P&L to Excel
3. Export dashboard to PDF
4. Download marketing data CSV (from Marketing page)
5. Verify files download and open correctly

**Expected Results**:
- [ ] Excel export downloads
- [ ] Excel file opens without errors
- [ ] Data looks correct in Excel
- [ ] PDF export downloads
- [ ] PDF is readable
- [ ] CSV exports work

**Pass/Fail**: ______
**Notes**: _________________________________

---

## 🔍 Cross-Cutting Tests

### TEST 16: Navigation & UI Consistency

**Objective**: Verify consistent UX across pages

**Steps**:
1. Navigate through all 15 pages sequentially
2. Check for visual consistency
3. Verify data persists across page changes

**Expected Results**:
- [ ] All pages load without errors
- [ ] Navigation menu always visible
- [ ] Page headers consistent
- [ ] Data doesn't reset when changing pages
- [ ] No broken layouts or overlapping elements
- [ ] Loading spinners appear for long operations

**Pass/Fail**: ______
**Notes**: _________________________________

---

### TEST 17: Performance

**Objective**: Verify acceptable performance

**Steps**:
1. Time initial file upload
2. Time P&L calculation
3. Time page navigation
4. Check for lag or freezing

**Expected Results**:
- [ ] File upload completes in <30 seconds
- [ ] Page navigation is instant (<2 seconds)
- [ ] Calculations complete in <10 seconds
- [ ] No noticeable lag in UI interactions
- [ ] Charts render smoothly

**Timings**:
- File upload: ______ seconds
- P&L calculation: ______ seconds
- Page navigation: ______ seconds

**Pass/Fail**: ______
**Notes**: _________________________________

---

### TEST 18: Mobile Responsiveness (Optional)

**Objective**: Test on mobile/tablet devices

**Steps**:
1. Open app on mobile device or use browser dev tools
2. Try basic navigation
3. Test key features (Dashboard, P&L View)

**Expected Results**:
- [ ] App loads on mobile
- [ ] Navigation menu accessible
- [ ] Key metrics visible
- [ ] Charts display (may need scrolling)
- [ ] Basic functionality works

**Pass/Fail**: ______
**Notes**: _________________________________

---

## 🐛 Issue Tracking

### Issue Template

For each issue found, record:

**Issue #**: ____
**Severity**: Critical / High / Medium / Low
**Page**: _________________________
**Description**:
_____________________________________________
_____________________________________________

**Steps to Reproduce**:
1.
2.
3.

**Expected**: _________________________
**Actual**: _________________________
**Screenshot/Evidence**: _________________________

---

### Known Issues (Reference Only)

These issues were recently fixed - verify they're resolved:

1. ✅ **FIXED**: P&L View showed £17.6M instead of £23.4M
   - Should now show £23.4M

2. ✅ **FIXED**: Waterfall showed Overheads as £0
   - Should now show non-zero overhead costs

3. ✅ **FIXED**: Scenario sliders didn't affect Detailed P&L
   - Should now apply changes to all revenue channels

---

## 📊 Test Summary

### Overall Results

**Total Tests**: 18
**Tests Passed**: ______
**Tests Failed**: ______
**Tests Skipped**: ______
**Pass Rate**: ______%

### Critical Tests Status

- [ ] Revenue totals match Excel (£23.4M)
- [ ] P&L View matches Dashboard
- [ ] Overheads show in Waterfall (non-zero)
- [ ] Marketing page displays correctly
- [ ] Data Quality score ≥80%

### Severity Breakdown

**Critical Issues**: ______ (blocks release)
**High Issues**: ______ (must fix before release)
**Medium Issues**: ______ (should fix)
**Low Issues**: ______ (nice to have)

---

## ✅ Sign-Off

### Tester Sign-Off

I have completed UAT testing of the Budget Planning App Version 1.0.1 and confirm:

- [ ] All critical tests passed
- [ ] Revenue calculations are accurate (match Excel)
- [ ] Overheads calculation is fixed (non-zero in Waterfall)
- [ ] Marketing page works correctly
- [ ] App is ready for production use

OR

- [ ] Critical issues found (see Issue Tracking section)
- [ ] App requires fixes before release

**Tester Name**: _________________________
**Date**: _________________________
**Signature**: _________________________

### Approval Sign-Off

Based on UAT results, I approve this release:

- [ ] **APPROVED** - Ready for production
- [ ] **APPROVED WITH MINOR ISSUES** - Deploy with known issues logged
- [ ] **REJECTED** - Requires fixes and re-test

**Approver Name**: _________________________
**Role**: _________________________
**Date**: _________________________
**Signature**: _________________________

---

## 📝 Notes & Feedback

### General Feedback

_____________________________________________
_____________________________________________
_____________________________________________

### Feature Requests

_____________________________________________
_____________________________________________
_____________________________________________

### Usability Observations

_____________________________________________
_____________________________________________
_____________________________________________

---

## 📞 Support Contacts

**Developer**: Claude Sonnet 4.5 (via Anthropic)
**Repository**: https://github.com/Rdwburns/budget-planning-app
**Documentation**: See PHASE1_SUMMARY.md and FOR_CLAUDE_CODE.md

**For Issues**: Create GitHub issue with:
- Test number
- Steps to reproduce
- Expected vs actual results
- Screenshot if applicable

---

**End of UAT Testing Guide**
