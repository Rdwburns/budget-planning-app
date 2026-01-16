"""
P&L Calculation Engine for Budget Planning App
Implements the same logic as the Excel model but in clean Python
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, field

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

    def calculate_b2b_revenue(self, territory: str = None, country_group: str = None) -> Dict[str, float]:
        """Calculate B2B revenue by month, optionally filtered"""
        b2b = self.data['b2b'].copy()

        if territory:
            b2b = b2b[b2b['Country'] == territory]
        elif country_group:
            b2b = b2b[b2b['Country Group'] == country_group]

        result = {}
        for col in self.dates:
            if col in b2b.columns:
                val = pd.to_numeric(b2b[col], errors='coerce').sum()
                # Apply scenario adjustment
                adj_key = f'b2b_revenue_{territory or country_group}'
                if adj_key in self.scenario:
                    val *= (1 + self.scenario[adj_key] / 100)
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

    def calculate_marketplace_revenue(self, territory: str) -> Dict[str, float]:
        """Calculate marketplace (Amazon) revenue for a territory"""
        amazon = self.data.get('amazon', pd.DataFrame())
        if amazon.empty:
            return {d: 0 for d in self.dates}

        # Get territory percentage allocation
        territory_row = amazon[amazon.iloc[:, 0] == territory]
        if territory_row.empty:
            return {d: 0 for d in self.dates}

        # Get total Amazon revenue (row index ~2 based on structure)
        total_row = amazon.iloc[1] if len(amazon) > 1 else None

        result = {}
        for col in self.dates:
            if col in amazon.columns and total_row is not None:
                total = float(total_row.get(col, 0) or 0)
                pct = float(territory_row[col].iloc[0]) if col in territory_row.columns else 0
                val = total * pct
                result[col] = val

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
            filtered = filtered[filtered['Territory'] == territory]
        if function:
            filtered = filtered[filtered['Function'] == function]

        result = {}
        for col in self.dates:
            if col in filtered.columns:
                val = pd.to_numeric(filtered[col], errors='coerce').sum()
                result[col] = val

        return result

    def calculate_territory_pl(self, territory: str) -> pd.DataFrame:
        """Calculate full P&L for a territory"""
        rows = []

        # Revenue
        dtc_rev = self.calculate_dtc_revenue(territory)
        b2b_rev = self.calculate_b2b_revenue(territory=territory)
        mp_rev = self.calculate_marketplace_revenue(territory)

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

    def calculate_combined_pl(self) -> pd.DataFrame:
        """Calculate combined P&L across all territories"""
        all_pls = {}
        territories = ['UK', 'ES', 'DE', 'IT', 'RO', 'CZ', 'HU', 'SK']

        for territory in territories:
            pl = self.calculate_territory_pl(territory)
            all_pls[territory] = pl

        # Sum all territories
        combined = all_pls[territories[0]].copy()
        for territory in territories[1:]:
            for col in self.dates:
                if col in combined.columns and col in all_pls[territory].columns:
                    combined[col] = combined[col] + all_pls[territory][col]

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
    if pd.isna(val) or val == 0:
        return "-"
    if val < 0:
        return f"({abs(val):,.0f})"
    return f"{val:,.0f}"


def format_percentage(val: float) -> str:
    """Format as percentage"""
    if pd.isna(val):
        return "-"
    return f"{val:.1%}"
