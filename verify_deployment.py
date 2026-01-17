"""
Deployment Verification Script
Run this to diagnose P&L revenue calculation issues
"""

def check_calculations_module():
    """Check what's in the calculations module"""
    print("=" * 70)
    print("DEPLOYMENT VERIFICATION REPORT")
    print("=" * 70)
    print()

    try:
        import calculations

        # Check version
        version = getattr(calculations, '__version__', 'NOT FOUND')
        print(f"✓ calculations.py imported successfully")
        print(f"  Version: {version}")
        print()

        # Check if PLCalculator exists
        if hasattr(calculations, 'PLCalculator'):
            print(f"✓ PLCalculator class found")

            # Check for calculate_combined_pl method
            calc_class = calculations.PLCalculator
            if hasattr(calc_class, 'calculate_combined_pl'):
                print(f"✓ calculate_combined_pl method exists")

                # Try to inspect the method to see if we can find the territory list
                import inspect
                source = inspect.getsource(calc_class.calculate_combined_pl)

                # Look for territory list
                if "territories = [" in source:
                    # Extract the territory list line
                    for line in source.split('\n'):
                        if 'territories = [' in line:
                            print(f"\n📍 Territory list found:")
                            print(f"  {line.strip()}")

                            # Count territories
                            territory_count = line.count("'")// 2
                            print(f"\n📊 Territory count: {territory_count}")

                            if territory_count == 14:
                                print(f"  ✅ CORRECT - Should have 14 territories")
                            elif territory_count == 8:
                                print(f"  ❌ WRONG - Has 8 territories (OLD CODE)")
                                print(f"  Missing ~£5.8M revenue!")
                            else:
                                print(f"  ⚠️ UNEXPECTED - Expected 8 or 14")

                            print()
                            print("Expected territories:")
                            expected = ['UK', 'ES', 'DE', 'IT', 'FR', 'RO', 'PL',
                                       'CZ', 'HU', 'SK', 'Other EU', 'US', 'AU', 'ROW']
                            print(f"  {expected}")
                            print(f"  Count: {len(expected)}")
                            break
                else:
                    print(f"  ⚠️ Territory list not found in expected format")

            else:
                print(f"✗ calculate_combined_pl method NOT FOUND")
        else:
            print(f"✗ PLCalculator class NOT FOUND")

    except ImportError as e:
        print(f"✗ Failed to import calculations.py")
        print(f"  Error: {e}")
    except Exception as e:
        print(f"✗ Error during verification:")
        print(f"  {e}")

    print()
    print("=" * 70)
    print("RECOMMENDATION:")
    print("=" * 70)

    if version == "1.0.2":
        print("✅ Version 1.0.2 is loaded - force redeploy SUCCESS")
    elif version == "1.0.1":
        print("⚠️ Version 1.0.1 loaded - force redeploy has NOT taken effect")
        print("   Wait 5 more minutes and try again")
    else:
        print("❌ Unexpected version - check deployment logs")

    print()


def check_live_calculation():
    """Test the calculation with mock data to see what territory count is used"""
    print("=" * 70)
    print("LIVE CALCULATION TEST")
    print("=" * 70)
    print()

    try:
        from calculations import PLCalculator
        import pandas as pd

        # Create minimal mock data
        mock_data = {
            'dates': ['2026-02', '2026-03'],
            'b2b': pd.DataFrame({
                'Country': ['United Kingdom', 'Spain', 'Germany'],
                '2026-02': [1000, 2000, 3000],
                '2026-03': [1000, 2000, 3000]
            }),
            'dtc': {
                'UK': pd.DataFrame({
                    'Metric': ['Total Revenue'],
                    '2026-02': [5000],
                    '2026-03': [5000]
                })
            },
            'amazon': pd.DataFrame({
                'Territory': ['UK'],
                '2026-02': [500],
                '2026-03': [500]
            }),
            'fulfilment': pd.DataFrame({
                'Country': ['UK'],
                'Channel': ['DTC'],
                'Rate': [-0.15]
            }),
            'overheads': pd.DataFrame({
                'Territory': ['UK'],
                'Function': ['Marketing'],
                '2026-02': [-100],
                '2026-03': [-100]
            })
        }

        calc = PLCalculator(mock_data)

        print("✓ PLCalculator instantiated with mock data")
        print("✓ Running calculate_combined_pl()...")

        result = calc.calculate_combined_pl()

        print(f"✓ Calculation completed")
        print(f"  Result shape: {result.shape}")
        print(f"  Columns: {list(result.columns)}")

        # Check if we can find total revenue
        if ('Revenue', 'Total Revenue') in result.index:
            total_rev_row = result.loc[('Revenue', 'Total Revenue')]
            total = total_rev_row.sum()
            print(f"\n📊 Mock Total Revenue: £{total:,.0f}")
            print(f"  Expected: £13,000 (if 3 territories processed)")
            print(f"  Actual:   £{total:,.0f}")

            if abs(total - 13000) < 100:
                print(f"  ✅ LOOKS CORRECT")
            else:
                print(f"  ⚠️ Unexpected value")

    except Exception as e:
        print(f"✗ Error during live calculation test:")
        print(f"  {e}")
        import traceback
        traceback.print_exc()

    print()


if __name__ == "__main__":
    check_calculations_module()
    print()
    check_live_calculation()

    print()
    print("=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print()
    print("1. If version is 1.0.2 and territory count is 14:")
    print("   → Upload Excel file and check P&L View revenue")
    print()
    print("2. If version is NOT 1.0.2:")
    print("   → Wait for Streamlit Cloud to deploy (2-5 minutes)")
    print("   → Hard refresh browser (Cmd+Shift+R)")
    print()
    print("3. If version is 1.0.2 but territory count is 8:")
    print("   → CRITICAL: Streamlit cached old version of calculations.py")
    print("   → Contact Streamlit Support to clear cache")
    print()
