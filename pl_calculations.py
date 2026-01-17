"""
P&L Calculation Engine for Budget Planning App
Implements the same logic as the Excel model but in clean Python
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, field

# Version: 1.0.9 - Use Country Group column for Other EU (EE+CE) and ROW
__version__ = "1.0.9"

@dataclass
class PLLineItem:
    """A single P&L line item with monthly values"""
    name: str
    category: str
    values: Dict[str, float] = field(default_factory=dict)

    def total(self) -> float:
        return sum(self.values.values())

    def to_series(self) -> pd.Series:
        return pd.Series(self.values, name=self.name)


class PLCalculator:
    """Calculates P&L from input data"""

    def __init__(self, data: dict, scenario_adjustments: dict = None):
        self.data = data
        self.scenario = scenario_adjustments or {}
        self.dates = data.get('dates', [])
        self.cogs_rates = data.get('cogs_rates', {
            'DTC': 0.24, 'B2B': 0.26, 'Marketplace': 0.18, 'TikTok': 0.24
        })

        # Territory code to B2B country name mapping
        self.territory_to_country = {
            'UK': 'United Kingdom',
            'ES': 'Spain',
            'DE': 'Germany',
            'IT': 'Italy',
            'FR': 'France',
            'RO': 'Romania',
            'PL': 'Poland',
            'CZ': 'Czech Republic',
            'HU': 'Hungary',
            'SK': 'Slovakia',
        }

    def calculate_b2b_revenue(self, territory: str = None, country_group: str = None, debug=False) -> Dict[str, float]:
        """Calculate B2B revenue by month, optionally filtered"""
        b2b_original = self.data['b2b'].copy()
        b2b = b2b_original.copy()

        if territory:
            # Special handling for grouping territories
            if territory == 'US':
                # Try multiple variations for United States
                b2b = b2b_original[b2b_original['Country'].isin(['United States', 'US', 'USA'])].copy()
                search_attempts = "United States OR US OR USA"
            elif territory == 'Other EU':
                # Aggregate Eastern Europe (EE) and Central Europe (CE) from Country Group column
                if 'Country Group' in b2b_original.columns:
                    b2b = b2b_original[b2b_original['Country Group'].isin(['EE', 'CE'])].copy()
                    ee_countries = b2b[b2b['Country Group'] == 'EE']['Country'].unique().tolist() if len(b2b) > 0 else []
                    ce_countries = b2b[b2b['Country Group'] == 'CE']['Country'].unique().tolist() if len(b2b) > 0 else []
                    search_attempts = f"OTHER EU (Country Group = EE or CE): {len(ee_countries)} EE + {len(ce_countries)} CE countries"
                else:
                    b2b = pd.DataFrame()  # No Country Group column
                    search_attempts = "OTHER EU (ERROR: No Country Group column found)"
            elif territory == 'ROW':
                # Rest of World from Country Group column
                if 'Country Group' in b2b_original.columns:
                    b2b = b2b_original[b2b_original['Country Group'] == 'ROW'].copy()
                    search_attempts = f"ROW (Country Group = ROW)"
                else:
                    b2b = pd.DataFrame()  # No Country Group column
                    search_attempts = "ROW (ERROR: No Country Group column found)"
            else:
                # Standard territory handling
                # TRY BOTH: Excel B2B sheet is inconsistent (some use codes, some use full names)
                country_name = self.territory_to_country.get(territory, territory)

                # Try full name first
                b2b = b2b_original[b2b_original['Country'] == country_name].copy()

                # If not found, try the territory code itself
                if len(b2b) == 0:
                    b2b = b2b_original[b2b_original['Country'] == territory].copy()

                search_attempts = f"{country_name} OR {territory}" if country_name != territory else country_name

            # DEBUG: Track B2B matching
            if debug:
                self._b2b_debug = self._b2b_debug if hasattr(self, '_b2b_debug') else {}
                available_countries = b2b_original['Country'].unique().tolist() if 'Country' in b2b_original.columns else []
                revenue_found = sum([pd.to_numeric(b2b[col], errors='coerce').sum() for col in self.dates if col in b2b.columns])

                # Get matched countries with their country groups
                countries_matched = []
                if len(b2b) > 0 and 'Country' in b2b.columns:
                    if 'Country Group' in b2b.columns:
                        for _, row in b2b[['Country', 'Country Group']].drop_duplicates().iterrows():
                            countries_matched.append(f"{row['Country']} ({row['Country Group']})")
                    else:
                        countries_matched = b2b['Country'].unique().tolist()

                self._b2b_debug[territory] = {
                    'searching_for': search_attempts,
                    'available_in_excel': available_countries,
                    'found': len(b2b) > 0,
                    'revenue': revenue_found,
                    'countries_matched': countries_matched
                }
        elif country_group:
            b2b = b2b[b2b['Country Group'] == country_group]

        result = {}
        for col in self.dates:
            if col in b2b.columns:
                val = pd.to_numeric(b2b[col], errors='coerce').sum()
                # Apply scenario adjustment (use 'b2b_growth' key from scenario planning)
                if 'b2b_growth' in self.scenario:
                    val *= (1 + self.scenario['b2b_growth'] / 100)
                result[col] = val

        return result

    def calculate_dtc_revenue(self, territory: str) -> Dict[str, float]:
        """Calculate DTC revenue for a territory"""
        if territory not in self.data.get('dtc', {}):
            return {d: 0 for d in self.dates}

        dtc = self.data['dtc'][territory]
        revenue_row = dtc[dtc['Metric'] == 'Total Revenue']

        result = {}
        for col in self.dates:
            if col in revenue_row.columns:
                val = float(revenue_row[col].iloc[0]) if len(revenue_row) > 0 else 0
                # Apply scenario adjustment
                adj_key = f'dtc_revenue_{territory}'
                if adj_key in self.scenario:
                    val *= (1 + self.scenario[adj_key] / 100)
                result[col] = val

        return result

    def calculate_marketplace_revenue(self, territory: str, debug=False) -> Dict[str, float]:
        """Calculate marketplace (Amazon) revenue for a territory"""
        amazon = self.data.get('amazon', pd.DataFrame())
        if amazon.empty:
            if debug:
                self._mp_debug = self._mp_debug if hasattr(self, '_mp_debug') else {}
                self._mp_debug[territory] = "Amazon sheet empty"
            return {d: 0 for d in self.dates}


        # Map territory codes to full names used in Amazon sheet
        territory_name_map = {
            'UK': 'UK',
            'ES': 'Spain',
            'DE': 'Germany',
            'IT': 'Italy',
            'FR': 'France',
            'RO': 'Romania',
            'PL': 'Poland',
            'CZ': 'Czech Republic',
            'HU': 'Hungary',
            'SK': 'Slovakia',
            'Other EU': 'Other EU',
            'US': 'United States',
            'AU': 'Australia',
            'ROW': 'Other RoW',
        }

        territory_name = territory_name_map.get(territory, territory)

        # Find the "Territory £" section which has revenue values (not percentages)
        # The revenue rows start after row 21 (Territory £ header)
        territory_gbp_idx = amazon[amazon.iloc[:, 0] == 'Territory £'].index
        if len(territory_gbp_idx) > 0:
            start_idx = territory_gbp_idx[0] + 1
            # Search in the revenue section (rows 22-35 approximately)
            revenue_section = amazon.iloc[start_idx:start_idx+15]
            territory_row = revenue_section[revenue_section.iloc[:, 0] == territory_name]

            # DEBUG: Store available territory names
            if debug:
                self._mp_debug = self._mp_debug if hasattr(self, '_mp_debug') else {}
                available_territories = revenue_section.iloc[:, 0].dropna().tolist()
                self._mp_debug[territory] = {
                    'searching_for': territory_name,
                    'available_in_excel': available_territories,
                    'found': not territory_row.empty
                }
        else:
            # Fallback: search entire sheet
            territory_row = amazon[amazon.iloc[:, 0] == territory_name]

            if debug:
                self._mp_debug = self._mp_debug if hasattr(self, '_mp_debug') else {}
                self._mp_debug[territory] = "Territory £ section not found in Amazon sheet"

        if territory_row.empty:
            return {d: 0 for d in self.dates}

        result = {}
        for col in self.dates:
            if col in territory_row.columns:
                val = territory_row[col].iloc[0]
                # Handle None/NaN values
                if pd.isna(val):
                    val = 0
                else:
                    val = float(val)

                # Apply scenario adjustment (use 'mp_growth' key from scenario planning)
                if 'mp_growth' in self.scenario:
                    val *= (1 + self.scenario['mp_growth'] / 100)

                result[col] = val
            else:
                result[col] = 0

        return result

    def calculate_total_marketplace_revenue(self) -> Dict[str, float]:
        """Calculate total marketplace (Amazon) revenue across ALL territories"""
        # All marketplace territories (codes used internally)
        marketplace_territories = ['UK', 'FR', 'ES', 'DE', 'IT', 'RO', 'PL', 'CZ', 'SK', 'HU',
                                'Other EU', 'US', 'AU', 'ROW']

        result: Dict[str, float] = {d: 0.0 for d in self.dates}
        for territory in marketplace_territories:
            territory_rev = self.calculate_marketplace_revenue(territory)
            for col in self.dates:
                result[col] += territory_rev.get(col, 0.0)

        return result

    def calculate_cogs(self, revenue: Dict[str, float], channel: str) -> Dict[str, float]:
        """Calculate Cost of Goods Sold"""
        rate = self.cogs_rates.get(channel, 0.24)

        # Apply scenario adjustment to COGS rate
        adj_key = f'cogs_rate_{channel}'
        if adj_key in self.scenario:
            rate = self.scenario[adj_key]

        return {k: -abs(v * rate) for k, v in revenue.items()}

    def calculate_fulfilment(self, revenue: Dict[str, float], territory: str, channel: str) -> Dict[str, float]:
        """Calculate fulfilment costs"""
        fulfilment = self.data.get('fulfilment', pd.DataFrame())

        # Find the rate for this territory/channel combo
        rate = -0.15  # default
        if not fulfilment.empty:
            match = fulfilment[(fulfilment['Country'] == territory) & (fulfilment['Channel'] == channel)]
            if not match.empty:
                rate = float(match['Rate'].iloc[0])

        # Apply scenario adjustment
        adj_key = f'fulfilment_rate_{territory}_{channel}'
        if adj_key in self.scenario:
            rate = self.scenario[adj_key]

        return {k: v * rate for k, v in revenue.items()}

    def calculate_overheads(self, territory: str = None, function: str = None) -> Dict[str, float]:
        """Calculate overhead costs"""
        oh = self.data.get('overheads', pd.DataFrame())
        if oh.empty:
            return {d: 0 for d in self.dates}

        filtered = oh.copy()
        if territory:
            # Apply territory name mapping (same as B2B)
            territory_name = self.territory_to_country.get(territory, territory)
            # Try both the mapped name and the original code
            filtered = filtered[
                (filtered['Territory'] == territory_name) |
                (filtered['Territory'] == territory)
            ]
        if function:
            filtered = filtered[filtered['Function'] == function]

        result = {}
        for col in self.dates:
            if col in filtered.columns:
                val = pd.to_numeric(filtered[col], errors='coerce').sum()
                result[col] = val

        return result

    def calculate_territory_pl(self, territory: str, debug=False) -> pd.DataFrame:
        """Calculate full P&L for a territory"""
        rows = []

        # Revenue
        dtc_rev = self.calculate_dtc_revenue(territory)
        b2b_rev = self.calculate_b2b_revenue(territory=territory, debug=debug)
        mp_rev = self.calculate_marketplace_revenue(territory, debug=debug)

        rows.append({'Line': 'DTC Revenue', 'Category': 'Revenue', **dtc_rev})
        rows.append({'Line': 'B2B Revenue', 'Category': 'Revenue', **b2b_rev})
        rows.append({'Line': 'Marketplace Revenue', 'Category': 'Revenue', **mp_rev})

        total_rev = {k: dtc_rev.get(k, 0) + b2b_rev.get(k, 0) + mp_rev.get(k, 0) for k in self.dates}
        rows.append({'Line': 'Total Revenue', 'Category': 'Revenue', **total_rev})

        # COGS
        dtc_cogs = self.calculate_cogs(dtc_rev, 'DTC')
        b2b_cogs = self.calculate_cogs(b2b_rev, 'B2B')
        mp_cogs = self.calculate_cogs(mp_rev, 'Marketplace')

        rows.append({'Line': 'DTC CoGS', 'Category': 'CoGS', **dtc_cogs})
        rows.append({'Line': 'B2B CoGS', 'Category': 'CoGS', **b2b_cogs})
        rows.append({'Line': 'Marketplace CoGS', 'Category': 'CoGS', **mp_cogs})

        total_cogs = {k: dtc_cogs.get(k, 0) + b2b_cogs.get(k, 0) + mp_cogs.get(k, 0) for k in self.dates}
        rows.append({'Line': 'Total CoGS', 'Category': 'CoGS', **total_cogs})

        # CM1 (Contribution Margin 1)
        dtc_cm1 = {k: dtc_rev.get(k, 0) + dtc_cogs.get(k, 0) for k in self.dates}
        b2b_cm1 = {k: b2b_rev.get(k, 0) + b2b_cogs.get(k, 0) for k in self.dates}
        mp_cm1 = {k: mp_rev.get(k, 0) + mp_cogs.get(k, 0) for k in self.dates}

        rows.append({'Line': 'DTC CM1', 'Category': 'CM1', **dtc_cm1})
        rows.append({'Line': 'B2B CM1', 'Category': 'CM1', **b2b_cm1})
        rows.append({'Line': 'Marketplace CM1', 'Category': 'CM1', **mp_cm1})

        total_cm1 = {k: dtc_cm1.get(k, 0) + b2b_cm1.get(k, 0) + mp_cm1.get(k, 0) for k in self.dates}
        rows.append({'Line': 'Total CM1', 'Category': 'CM1', **total_cm1})

        # Fulfilment
        dtc_ful = self.calculate_fulfilment(dtc_rev, territory, 'DTC')
        b2b_ful = self.calculate_fulfilment(b2b_rev, territory, 'B2B')
        mp_ful = self.calculate_fulfilment(mp_rev, territory, 'Marketplace')

        rows.append({'Line': 'DTC Fulfilment', 'Category': 'Fulfilment', **dtc_ful})
        rows.append({'Line': 'B2B Fulfilment', 'Category': 'Fulfilment', **b2b_ful})
        rows.append({'Line': 'Marketplace Fulfilment', 'Category': 'Fulfilment', **mp_ful})

        total_ful = {k: dtc_ful.get(k, 0) + b2b_ful.get(k, 0) + mp_ful.get(k, 0) for k in self.dates}
        rows.append({'Line': 'Total Fulfilment', 'Category': 'Fulfilment', **total_ful})

        # CM2
        total_cm2 = {k: total_cm1.get(k, 0) + total_ful.get(k, 0) for k in self.dates}
        rows.append({'Line': 'Total CM2', 'Category': 'CM2', **total_cm2})

        # Overheads
        overheads = self.calculate_overheads(territory=territory)
        rows.append({'Line': 'Overheads', 'Category': 'Overheads', **overheads})

        # EBITDA
        ebitda = {k: total_cm2.get(k, 0) + overheads.get(k, 0) for k in self.dates}
        rows.append({'Line': 'EBITDA', 'Category': 'EBITDA', **ebitda})

        df = pd.DataFrame(rows)
        df = df.set_index(['Category', 'Line'])

        return df

    def calculate_combined_pl(self, debug=False) -> pd.DataFrame:
        """Calculate combined P&L across all territories"""
        all_pls = {}
        # Include ALL territories with DTC, B2B, or Marketplace revenue
        # This includes DTC territories (UK, ES, IT, RO, CZ, HU, SK, Other EU)
        # and marketplace-only territories (FR, DE, PL, US, AU, ROW)
        # CRITICAL FIX: Expanded from 8 to 14 territories to get full £23.4M revenue
        territories = ['UK', 'ES', 'DE', 'IT', 'FR', 'RO', 'PL', 'CZ', 'HU', 'SK', 'Other EU', 'US', 'AU', 'ROW']

        # DEBUG: Track revenue by territory
        territory_revenues = {}

        for territory in territories:
            pl = self.calculate_territory_pl(territory, debug=debug)
            all_pls[territory] = pl

            # DEBUG: Extract total revenue for this territory
            if ('Revenue', 'Total Revenue') in pl.index:
                total_rev = pl.loc[('Revenue', 'Total Revenue')].sum()
                territory_revenues[territory] = total_rev
            else:
                territory_revenues[territory] = 0

        # Store debug info if requested
        if debug:
            self._debug_territory_revenues = territory_revenues

        # Sum all territories
        combined = all_pls[territories[0]].copy()
        for territory in territories[1:]:
            for col in self.dates:
                if col in combined.columns and col in all_pls[territory].columns:
                    combined[col] = combined[col] + all_pls[territory][col]

        # Add Group/Shared level overheads (like central marketing) that aren't allocated to territories
        oh = self.data.get('overheads', pd.DataFrame())
        if not oh.empty and 'Territory' in oh.columns:
            # Find overheads with Territory = 'Group', 'Shared', 'Central', or similar
            group_overheads = oh[
                oh['Territory'].isin(['Group', 'Shared', 'Central', 'Corporate', 'HQ']) |
                oh['Territory'].isna()
            ]

            if not group_overheads.empty:
                group_oh_values = {}
                for col in self.dates:
                    if col in group_overheads.columns:
                        val = pd.to_numeric(group_overheads[col], errors='coerce').sum()
                        group_oh_values[col] = val

                # Add to combined overheads
                if ('Overheads', 'Overheads') in combined.index:
                    for col in self.dates:
                        if col in combined.columns:
                            combined.loc[('Overheads', 'Overheads'), col] += group_oh_values.get(col, 0)

                # Recalculate EBITDA with new overheads
                if ('CM2', 'Total CM2') in combined.index and ('EBITDA', 'EBITDA') in combined.index:
                    for col in self.dates:
                        if col in combined.columns:
                            cm2 = combined.loc[('CM2', 'Total CM2'), col]
                            overheads = combined.loc[('Overheads', 'Overheads'), col]
                            combined.loc[('EBITDA', 'EBITDA'), col] = cm2 + overheads

        return combined

    def calculate_scenario_comparison(self, base_scenario: dict, new_scenario: dict) -> pd.DataFrame:
        """Compare two scenarios"""
        base_calc = PLCalculator(self.data, base_scenario)
        new_calc = PLCalculator(self.data, new_scenario)

        base_pl = base_calc.calculate_combined_pl()
        new_pl = new_calc.calculate_combined_pl()

        # Calculate difference
        diff = new_pl.copy()
        for col in self.dates:
            if col in diff.columns:
                diff[col] = new_pl[col] - base_pl[col]

        return {
            'base': base_pl,
            'new': new_pl,
            'difference': diff
        }


def format_currency(val: float) -> str:
    """Format as currency"""
    if pd.isna(val):
        return "-"
    if val == 0:
        return "£0"
    if val < 0:
        return f"(£{abs(val):,.0f})"
    return f"£{val:,.0f}"


def format_percentage(val: float) -> str:
    """Format as percentage"""
    if pd.isna(val):
        return "-"
    return f"{val:.1%}"
