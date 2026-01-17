# Budget Planning App - Release Notes v1.0.1

**Release Date**: 2026-01-17
**Status**: ✅ Production Ready
**Commit**: 31558f0

---

## 🎉 What's New

### 1. Marketing Management Page (📣)

**NEW**: Dedicated marketing budget analysis and ROI tracking

**Features**:
- **Marketing Overview**: Total budget, % of revenue, ROI metrics
- **Territory Analysis**: Spend breakdown by territory with charts
- **Monthly Trends**: Visual trend analysis across time
- **ROI Analysis**: Revenue per £1 marketing by territory
- **Scenario Modeling**: Test impact of budget changes
- **Data Export**: Download marketing data as CSV

**Access**: Navigate to "📣 Marketing" in sidebar

**Use Cases**:
- Track marketing efficiency by territory
- Identify best ROI territories
- Model budget allocation scenarios
- Export for board presentations

---

### 2. UAT Testing Guide

**NEW**: Comprehensive testing checklist for QA/UAT

**Includes**:
- 18 detailed test scenarios with pass/fail criteria
- Critical tests for revenue accuracy
- Performance benchmarks
- Issue tracking template
- Tester and approver sign-off sections

**File**: `UAT_TESTING_GUIDE.md`

**Use For**:
- Pre-release testing
- Production readiness validation
- Quality assurance
- Bug tracking

---

## 🐛 Bug Fixes

### 1. Overheads Calculation Fixed

**Problem**: Waterfall Analysis showed Overheads as £0

**Root Cause**:
- Territory name mismatch (same issue as B2B)
- Missing group-level overheads (marketing, shared costs)

**Solution**:
- Added territory mapping to `calculate_overheads()`
- Enhanced `calculate_combined_pl()` to include Group/Shared overheads
- Recalculates EBITDA with complete overhead costs

**Impact**: Waterfall now shows correct overhead costs including marketing

**Commit**: f6867c6

---

## 📊 Complete Feature List

### Core Features (Existing)
1. ✅ Dashboard - Revenue KPIs and channel breakdown
2. ✅ Revenue Inputs - Manage revenue forecasts
3. ✅ B2B Management - Customer revenue tracking
4. ✅ Cost Management - Cost allocation and tracking
5. ✅ Scenario Planning - Model what-if scenarios
6. ✅ P&L View - Detailed P&L by territory/channel
7. ✅ Budget vs Actuals - Variance analysis
8. ✅ Version Control - Save and compare versions
9. ✅ Sensitivity Analysis - Test input sensitivities
10. ✅ Export - Download data and reports

### Phase 1 Collaboration Features (NEW)
11. ✅ Comments & Notes - Team collaboration
12. ✅ Assumptions Register - Document the "why"
13. ✅ Data Quality Dashboard - Validation and quality score
14. ✅ Waterfall Analysis - Visual P&L breakdown

### Latest Additions
15. ✅ **Marketing Management** - ROI and spend analysis (NEW v1.0.1)

---

## 🎯 Critical Test Points

### Must Verify Before Use

1. **Revenue Accuracy** ✅
   - Dashboard shows: £23.4M total
   - P&L View shows: £23.4M total
   - Breakdown: B2B £7.6M, DTC £12.5M, Marketplace £3.3M

2. **Overheads in Waterfall** ✅
   - Waterfall shows non-zero overheads (was £0 before fix)
   - Includes marketing costs
   - EBITDA calculates correctly

3. **Marketing Page** ✅
   - Shows total marketing budget
   - Territory breakdown displays
   - ROI calculations work

4. **Data Quality** ✅
   - Quality score ≥80%
   - All territories present
   - No critical issues

---

## 📝 UAT Test Checklist (Quick Version)

For full checklist, see `UAT_TESTING_GUIDE.md`

### Priority 1: Critical Tests
- [ ] Upload Excel file successfully
- [ ] Dashboard shows £23.4M total revenue
- [ ] P&L View shows £23.4M (matches Dashboard)
- [ ] Waterfall shows non-zero overheads
- [ ] Marketing page displays correctly

### Priority 2: Feature Tests
- [ ] Data Quality score ≥80%
- [ ] Comments system works (add/delete)
- [ ] Assumptions register works (add/delete)
- [ ] Scenario Planning applies changes
- [ ] Version Control saves/restores

### Priority 3: Export & Performance
- [ ] Excel export works
- [ ] Marketing CSV export works
- [ ] File upload <30 seconds
- [ ] Page navigation <2 seconds

---

## 🚀 Deployment Status

**Current Version**: 1.0.1 (commit 31558f0)
**Deployment**: Automatic via Streamlit Cloud
**ETA**: 2-3 minutes after push

**To Verify Deployment**:
1. Hard refresh browser (Cmd+Shift+R / Ctrl+Shift+R)
2. Check sidebar for version badge: "✨ Version 1.0.1"
3. Look for "📣 Marketing" in navigation menu

---

## 📚 Documentation

### User Documentation
- **SUGGESTED_FEATURES.md** - Full roadmap (27 features)
- **PHASE1_SUMMARY.md** - Phase 1 implementation details
- **UAT_TESTING_GUIDE.md** - Comprehensive testing checklist

### Developer Documentation
- **FOR_CLAUDE_CODE.md** - Quick reference for future development
- **README.md** - Project overview and setup

### Technical Files
- **app.py** - Main application (2746 lines)
- **calculations.py** - P&L calculation engine
- **data_loader.py** - Excel data loading
- **features_phase1.py** - Phase 1 features
- **marketing_module.py** - Marketing management (NEW)

---

## 🔧 Technical Changes

### Files Modified
1. **calculations.py**
   - Added territory mapping to `calculate_overheads()` (lines 204-210)
   - Enhanced `calculate_combined_pl()` to include group overheads (lines 310-338)

2. **app.py**
   - Added Marketing to navigation menu (line 113)
   - Added Marketing page routing (line 2724)
   - Imported `render_marketing_management`

3. **marketing_module.py** (NEW)
   - Complete marketing analysis module
   - 6 major features in single page
   - Extracts data from DTC sheets and Overheads

### Database Changes
None - all features use session state (in-memory)

### API Changes
None - purely frontend enhancements

---

## ⚠️ Known Limitations

1. **Session State Only**: No database persistence yet (Phase 5)
2. **No User Auth**: All comments show "Current User"
3. **Single User**: No real-time collaboration
4. **Marketing Data**: Requires data in DTC sheets or Overheads

---

## 🎯 Next Steps (Phase 2)

See SUGGESTED_FEATURES.md for complete roadmap

**High Priority**:
1. Enhanced Variance Analysis (volume/price/mix)
2. Key Driver Analysis (tornado charts)
3. Bulk Operations (copy months, smart fill)

---

## 📞 Support

**Issues**: Create GitHub issue with test number and steps to reproduce
**Documentation**: See FOR_CLAUDE_CODE.md for developer context
**UAT Questions**: Reference UAT_TESTING_GUIDE.md test numbers

---

## ✅ Sign-Off Checklist

### Pre-Release Checklist
- [x] All critical bug fixes tested
- [x] New features implemented
- [x] Documentation updated
- [x] UAT guide created
- [x] Code committed and pushed
- [x] Version badge updated

### Post-Release Checklist
- [ ] Verify deployment (check version badge)
- [ ] Run critical UAT tests
- [ ] Verify revenue totals (£23.4M)
- [ ] Check overheads in waterfall (non-zero)
- [ ] Test marketing page
- [ ] User acceptance sign-off

---

**Release Manager**: Claude Sonnet 4.5
**Approved By**: ___________________________
**Date**: _________________________________

---

## 📊 Metrics to Track

After deployment, monitor:

1. **Accuracy**: Revenue calculations match Excel (£23.4M)
2. **Usage**: % of users accessing new Marketing page
3. **Quality**: Data Quality scores
4. **Performance**: Page load times
5. **Feedback**: User comments and issues

---

**End of Release Notes**

For detailed testing instructions, see UAT_TESTING_GUIDE.md
For future development context, see FOR_CLAUDE_CODE.md
