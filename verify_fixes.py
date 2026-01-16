"""
Verification script to confirm audit fixes
Expected results from audit.md:
- B2B: £7,567,798
- DTC: £12,526,999
- Marketplace: £3,304,438
- Total: £23,399,235
"""
from data_loader import load_all_data
from calculations import PLCalculator
from pathlib import Path

def verify_fixes():
    # Load data
    file_path = Path(__file__).parent / "Copy of Budget FY26-27 Base.xlsx"
    if not file_path.exists():
        print(f"❌ Excel file not found at: {file_path}")
        return

    print("Loading data...")
    data = load_all_data(str(file_path))
    calc = PLCalculator(data)

    print("\n" + "="*60)
    print("REVENUE VERIFICATION")
    print("="*60)

    # Verify B2B
    b2b_total = sum(calc.calculate_b2b_revenue().values())
    b2b_expected = 7567798
    b2b_match = abs(b2b_total - b2b_expected) < 100
    print(f"\n✓ B2B Revenue:")
    print(f"  Expected: £{b2b_expected:,.0f}")
    print(f"  Actual:   £{b2b_total:,.0f}")
    print(f"  Status:   {'✅ MATCH' if b2b_match else '❌ MISMATCH'}")

    # Verify DTC
    dtc_territories = ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK', 'Other EU']
    dtc_total = sum(sum(calc.calculate_dtc_revenue(t).values()) for t in dtc_territories)
    dtc_expected = 12526999
    dtc_match = abs(dtc_total - dtc_expected) < 100
    print(f"\n✓ DTC Revenue:")
    print(f"  Expected: £{dtc_expected:,.0f}")
    print(f"  Actual:   £{dtc_total:,.0f}")
    print(f"  Status:   {'✅ MATCH' if dtc_match else '❌ MISMATCH'}")

    # Show DTC breakdown
    print(f"  Breakdown by territory:")
    for territory in dtc_territories:
        if territory in data.get('dtc', {}):
            territory_rev = sum(calc.calculate_dtc_revenue(territory).values())
            print(f"    {territory}: £{territory_rev:,.0f}")

    # Verify Marketplace
    mp_total = sum(calc.calculate_total_marketplace_revenue().values())
    mp_expected = 3304438
    mp_match = abs(mp_total - mp_expected) < 100
    print(f"\n✓ Marketplace Revenue:")
    print(f"  Expected: £{mp_expected:,.0f}")
    print(f"  Actual:   £{mp_total:,.0f}")
    print(f"  Status:   {'✅ MATCH' if mp_match else '❌ MISMATCH'}")

    # Total
    total = b2b_total + dtc_total + mp_total
    total_expected = 23399235
    total_match = abs(total - total_expected) < 100
    print(f"\n✓ Total Revenue:")
    print(f"  Expected: £{total_expected:,.0f}")
    print(f"  Actual:   £{total:,.0f}")
    print(f"  Status:   {'✅ MATCH' if total_match else '❌ MISMATCH'}")

    print("\n" + "="*60)
    if all([b2b_match, dtc_match, mp_match, total_match]):
        print("✅ ALL CHECKS PASSED - Revenue calculations match Excel!")
    else:
        print("❌ SOME CHECKS FAILED - Review differences above")
    print("="*60 + "\n")

    # Show validation warnings if any
    if 'validation_warnings' in data and data['validation_warnings']:
        print("\n⚠️  Data Validation Warnings:")
        for warning in data['validation_warnings']:
            print(f"  - {warning}")

if __name__ == "__main__":
    verify_fixes()
