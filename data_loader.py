"""
Data loader module for Budget Planning App
Extracts and processes data from the Excel budget model
"""
import pandas as pd
from openpyxl import load_workbook
from datetime import datetime
import numpy as np

class BudgetDataLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.territories = ['UK', 'ES', 'DE', 'IT', 'FR', 'RO', 'CZ', 'HU', 'SK', 'Other EU', 'ROW']
        self.territory_groups = {
            'UK': 'UK',
            'ES': 'CE', 'DE': 'CE', 'IT': 'CE', 'FR': 'CE',
            'RO': 'EE', 'CZ': 'EE', 'HU': 'EE', 'SK': 'EE',
            'Other EU': 'CE', 'ROW': 'ROW'
        }
        self.channels = ['DTC', 'B2B', 'Marketplace', 'TikTok']

    def load_b2b_data(self) -> pd.DataFrame:
        """Load B2B customer revenue data"""
        df = pd.read_excel(self.file_path, sheet_name='B2B', header=5)

        # Clean column names - convert datetime to string
        new_cols = []
        for col in df.columns:
            if isinstance(col, datetime):
                new_cols.append(col.strftime('%Y-%m'))
            else:
                new_cols.append(str(col))
        df.columns = new_cols

        # Keep only relevant columns
        base_cols = ['Customer Name', 'Country', 'Country Group', 'Customer Margin', 'Last Year FY25 Revenue']
        date_cols = [c for c in df.columns if c.startswith('202')]
        df = df[base_cols + date_cols].copy()

        # Clean data
        df = df.dropna(subset=['Customer Name'])
        df['Customer Margin'] = pd.to_numeric(df['Customer Margin'], errors='coerce').fillna(0)

        # Convert all date columns to numeric
        for col in date_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        return df

    def load_overheads(self) -> pd.DataFrame:
        """Load overhead costs data"""
        df = pd.read_excel(self.file_path, sheet_name='Overheads', header=1)

        # Clean column names
        new_cols = []
        for col in df.columns:
            if isinstance(col, datetime):
                new_cols.append(col.strftime('%Y-%m'))
            else:
                new_cols.append(str(col))
        df.columns = new_cols

        # Keep structure columns and date columns
        base_cols = ['Territory', 'Function', 'Category', 'Group', 'Supplier']
        date_cols = [c for c in df.columns if c.startswith('202')]

        available_cols = [c for c in base_cols if c in df.columns] + date_cols
        df = df[available_cols].copy()
        df = df.dropna(subset=['Territory', 'Category'])

        # Convert all date columns to numeric
        for col in date_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        return df

    def load_fulfilment_rates(self) -> pd.DataFrame:
        """Load fulfilment cost rates by country and channel"""
        df = pd.read_excel(self.file_path, sheet_name='Fulfilment')
        # Handle column name with trailing space
        rate_col = [c for c in df.columns if 'fulfilment' in c.lower()][0] if any('fulfilment' in c.lower() for c in df.columns) else df.columns[2]
        df = df[['Country', 'Category', rate_col]].copy()
        df = df.rename(columns={'Category': 'Channel', rate_col: 'Rate'})
        df['Rate'] = pd.to_numeric(df['Rate'], errors='coerce').fillna(-0.15)
        return df

    def load_amazon_data(self) -> pd.DataFrame:
        """Load Amazon marketplace data"""
        df = pd.read_excel(self.file_path, sheet_name='Amazon', header=1)

        # Clean column names
        new_cols = []
        for col in df.columns:
            if isinstance(col, datetime):
                new_cols.append(col.strftime('%Y-%m'))
            else:
                new_cols.append(str(col))
        df.columns = new_cols

        # Convert all date columns to numeric
        date_cols = [c for c in df.columns if c.startswith('202')]
        for col in date_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        return df

    def load_payroll(self) -> pd.DataFrame:
        """Load payroll data"""
        df = pd.read_excel(self.file_path, sheet_name='Payroll', header=4)
        return df

    def load_dtc_inputs(self, territory: str) -> pd.DataFrame:
        """Load DTC input data for a specific territory"""
        if territory not in self.territories or territory == 'ROW':
            return pd.DataFrame()

        try:
            wb = load_workbook(self.file_path, read_only=True, data_only=True)
            ws = wb[territory]

            # Extract key metrics
            data = []
            metric_rows = {
                'Traffic': 4,
                'Conversion Rate': 6,
                'Total Orders': 13,
                'New Customers': 9,
                'New Subscription Customers': 10,
                'Recurring Subscription Customers': 11,
                'Returning Customers': 12,
                'Marketing Budget': 36,
                'Total Revenue': 25,
            }

            # Get month columns (starting from column 5)
            months = []
            for col in range(5, min(30, ws.max_column + 1)):
                val = ws.cell(row=2, column=col).value
                if val and isinstance(val, datetime):
                    months.append(val.strftime('%Y-%m'))

            for metric, row in metric_rows.items():
                row_data = {'Metric': metric, 'Territory': territory}
                for i, month in enumerate(months):
                    col = 5 + i
                    val = ws.cell(row=row, column=col).value
                    row_data[month] = val if val else 0
                data.append(row_data)

            wb.close()
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Error loading DTC for {territory}: {e}")
            return pd.DataFrame()

    def get_date_columns(self) -> list:
        """Get list of date columns from the model"""
        df = pd.read_excel(self.file_path, sheet_name='B2B', header=5, nrows=1)
        dates = []
        for col in df.columns:
            if isinstance(col, datetime):
                dates.append(col.strftime('%Y-%m'))
        return dates

    def load_cogs_rates(self) -> dict:
        """Load CoGS rates from UK P&L (used as defaults)"""
        wb = load_workbook(self.file_path, data_only=False)
        ws = wb['UK P&L']

        rates = {
            'DTC': abs(float(ws.cell(row=16, column=3).value or 0.24)),
            'B2B': abs(float(ws.cell(row=17, column=3).value or 0.26)),
            'Marketplace': abs(float(ws.cell(row=18, column=3).value or 0.18)),
            'TikTok': abs(float(ws.cell(row=19, column=3).value or 0.24)),
        }
        wb.close()
        return rates


def load_all_data(file_path: str) -> dict:
    """Load all data from the budget model"""
    loader = BudgetDataLoader(file_path)

    data = {
        'b2b': loader.load_b2b_data(),
        'overheads': loader.load_overheads(),
        'fulfilment': loader.load_fulfilment_rates(),
        'amazon': loader.load_amazon_data(),
        'cogs_rates': loader.load_cogs_rates(),
        'dates': loader.get_date_columns(),
        'territories': loader.territories,
        'territory_groups': loader.territory_groups,
        'channels': loader.channels,
    }

    # Load DTC data for each territory
    data['dtc'] = {}
    for territory in ['UK', 'ES', 'IT', 'RO', 'CZ', 'HU', 'SK']:
        dtc_data = loader.load_dtc_inputs(territory)
        if not dtc_data.empty:
            data['dtc'][territory] = dtc_data

    return data
