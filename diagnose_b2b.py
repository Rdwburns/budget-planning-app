#!/usr/bin/env python3
"""
Simple diagnostic to check B2B data country names
This will help confirm the territory mapping is correct
"""
import pandas as pd
from pathlib import Path

def diagnose():
    file_path = Path(__file__).parent / "Copy of Budget FY26-27 Base.xlsx"

    print("=" * 80)
    print("B2B DATA DIAGNOSTIC")
    print("=" * 80)

    try:
        # Load B2B sheet
        df = pd.read_excel(file_path, sheet_name='B2B', header=5)

        # Check if 'Country' column exists
        country_col = None
        for col in df.columns:
            if 'country' in str(col).lower() and 'group' not in str(col).lower():
                country_col = col
                break

        if country_col:
            print(f"\n✅ Found Country column: '{country_col}'")

            # Get unique countries
            countries = df[country_col].dropna().unique()
            print(f"\n📊 Unique countries in B2B data ({len(countries)}):")
            for country in sorted(countries):
                print(f"   - {country}")

            # Check what we're looking for
            print("\n🔍 Checking for territory codes vs full names:")
            codes = ['UK', 'ES', 'DE', 'IT', 'FR', 'RO', 'PL', 'CZ', 'HU', 'SK']
            for code in codes:
                if code in countries:
                    print(f"   ✅ Found '{code}' (short code)")
                else:
                    print(f"   ❌ NOT found '{code}' (need full name)")

            # Suggested mapping
            print("\n💡 Full country names found that match territory codes:")
            mapping_suggestions = {
                'United Kingdom': 'UK',
                'Spain': 'ES',
                'Germany': 'DE',
                'Italy': 'IT',
                'France': 'FR',
                'Romania': 'RO',
                'Poland': 'PL',
                'Czech Republic': 'CZ',
                'Hungary': 'HU',
                'Slovakia': 'SK'
            }
            for full_name, code in mapping_suggestions.items():
                if full_name in countries:
                    print(f"   '{code}' → '{full_name}' ✅")

        else:
            print("❌ Could not find Country column")
            print(f"Available columns: {list(df.columns[:10])}")

        print("\n" + "=" * 80)
        print("CONCLUSION:")
        print("=" * 80)
        print("If the B2B data uses full country names like 'United Kingdom',")
        print("then the territory_to_country mapping in calculations.py is CORRECT")
        print("and the issue is just that Streamlit Cloud needs to deploy the fix.")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose()
