#!/usr/bin/env python3
"""
Quick test to verify Excel source data calculations
This will help us determine if the issue is in data loading or just deployment lag
"""
import sys
import subprocess

# Try to import required modules
try:
    import pandas as pd
    from data_loader import load_all_data
    from calculations import PLCalculator
    from pathlib import Path
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Installing in user space...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "pandas", "openpyxl"])
    import pandas as pd
    from data_loader import load_all_data
    from calculations import PLCalculator
    from pathlib import Path

def main():
    file_path = Path(__file__).parent / "Copy of Budget FY26-27 Base.xlsx"

    if not file_path.exists():
        print(f"❌ Excel file not found: {file_path}")
        return

    print("=" * 80)
    print("EXCEL SOURCE DATA VERIFICATION")
    print("=" * 80)

    # Load data
    print("\n📂 Loading data from Excel...")
    data = load_all_data(str(file_path))
    calc = PLCalculator(data)

    print(f"   Date columns: {len(data['dates'])}")
    print(f"   Dates: {data['dates'][:3]}...{data['dates'][-3:]}")

    # Test 1: B2B Revenue - No Territory Filter (Dashboard method)
    print("\n" + "=" * 80)
    print("TEST 1: B2B Revenue - No Territory Filter (Dashboard Method)")
    print("=" * 80)
    b2b_total = sum(calc.calculate_b2b_revenue().values())
    print(f"   Total B2B Revenue: £{b2b_total:,.0f}")
    print(f"   Expected: £7,567,798")
    print(f"   Match: {'✅' if abs(b2b_total - 7567798) < 100 else '❌'}")

    # Test 2: B2B Revenue - By Territory (P&L Method)
    print("\n" + "=" * 80)
    print("TEST 2: B2B Revenue - By Territory (P&L Method)")
    print("=" * 80)
    territories = ['UK', 'ES', 'DE', 'IT', 'FR', 'RO', 'PL', 'CZ', 'HU', 'SK', 'Other EU', 'US', 'AU', 'ROW']
    b2b_by_territory = {}
    b2b_territory_total = 0

    for territory in territories:
        territory_b2b = sum(calc.calculate_b2b_revenue(territory=territory).values())
        if territory_b2b > 0:
            b2b_by_territory[territory] = territory_b2b
            b2b_territory_total += territory_b2b
            print(f"   {territory:12} : £{territory_b2b:>10,.0f}")

    print(f"\n   Total (sum of territories): £{b2b_territory_total:,.0f}")
    print(f"   Expected: £7,567,798")
    print(f"   Match: {'✅' if abs(b2b_territory_total - 7567798) < 100 else '❌'}")

    # Test 3: DTC Revenue
    print("\n" + "=" * 80)
    print("TEST 3: DTC Revenue")
    print("=" * 80)
    dtc_territories = ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK', 'Other EU']
    dtc_total = 0
    for territory in dtc_territories:
        territory_dtc = sum(calc.calculate_dtc_revenue(territory).values())
        if territory_dtc > 0:
            dtc_total += territory_dtc
            print(f"   {territory:12} : £{territory_dtc:>10,.0f}")

    print(f"\n   Total DTC Revenue: £{dtc_total:,.0f}")
    print(f"   Expected: £12,526,999")
    print(f"   Match: {'✅' if abs(dtc_total - 12526999) < 100 else '❌'}")

    # Test 4: Marketplace Revenue
    print("\n" + "=" * 80)
    print("TEST 4: Marketplace Revenue")
    print("=" * 80)
    mp_total = sum(calc.calculate_total_marketplace_revenue().values())
    print(f"   Total Marketplace Revenue: £{mp_total:,.0f}")
    print(f"   Expected: £3,304,438")
    print(f"   Match: {'✅' if abs(mp_total - 3304438) < 100 else '❌'}")

    # Test 5: Combined P&L (The failing method)
    print("\n" + "=" * 80)
    print("TEST 5: Combined P&L Total Revenue (P&L View Method)")
    print("=" * 80)
    combined_pl = calc.calculate_combined_pl()

    if ('Revenue', 'Total Revenue') in combined_pl.index:
        date_cols = [c for c in combined_pl.columns if c.startswith('202')]
        pl_total_revenue = combined_pl.loc[('Revenue', 'Total Revenue'), date_cols].sum()
        print(f"   P&L Total Revenue: £{pl_total_revenue:,.0f}")
        print(f"   Expected: £23,399,235")
        print(f"   Match: {'✅' if abs(pl_total_revenue - 23399235) < 100 else '❌'}")

        # Show revenue breakdown
        if ('Revenue', 'DTC Revenue') in combined_pl.index:
            pl_dtc = combined_pl.loc[('Revenue', 'DTC Revenue'), date_cols].sum()
            print(f"   - DTC Revenue: £{pl_dtc:,.0f}")
        if ('Revenue', 'B2B Revenue') in combined_pl.index:
            pl_b2b = combined_pl.loc[('Revenue', 'B2B Revenue'), date_cols].sum()
            print(f"   - B2B Revenue: £{pl_b2b:,.0f}")
        if ('Revenue', 'Marketplace Revenue') in combined_pl.index:
            pl_mp = combined_pl.loc[('Revenue', 'Marketplace Revenue'), date_cols].sum()
            print(f"   - Marketplace Revenue: £{pl_mp:,.0f}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total = b2b_total + dtc_total + mp_total
    print(f"   Dashboard Method Total: £{total:,.0f}")
    print(f"   P&L Method Total: £{pl_total_revenue:,.0f}")
    print(f"   Difference: £{abs(total - pl_total_revenue):,.0f}")
    print(f"   Expected Total: £23,399,235")

    if abs(pl_total_revenue - 23399235) < 100:
        print("\n   ✅ LOCAL CALCULATIONS ARE CORRECT!")
        print("   ⚠️  Issue is with Streamlit Cloud deployment - needs to pull latest code")
    else:
        print("\n   ❌ LOCAL CALCULATIONS STILL INCORRECT")
        print("   🔍 Further investigation needed in calculation logic")

    print("=" * 80)

if __name__ == "__main__":
    main()
