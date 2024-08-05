from datetime import datetime, timedelta
from qablet_contracts.bnd.fixed import FixedBond

def bond_dict_to_obj(bond):
    coupon = float(bond["Coupon"]) / 100
    accrual_start = datetime.strptime(bond["Accrual Start"], "%Y-%m-%d")
    maturity = datetime.strptime(bond["Maturity"], "%Y-%m-%d")
    frequency = f"{int(bond['Frequency'])}QE"
    currency = bond["Currency"]
    notional = float(bond["Notional"])

    bond_obj = FixedBond(currency, coupon, accrual_start, maturity, frequency)
    return bond_obj, notional

# Function to create a new bond with default values
def create_default_bond(index):
    DEFAULT_MENU = [
        {"label": "Delete", "value": 1},
        {"label": "Show Timetable", "value": 2},
    ]
    return {
        "Bond": f"Bond {index}",
        "Currency": "USD",
        "Coupon": 2.5,
        "Accrual Start": datetime.today().strftime("%Y-%m-%d"),
        "Maturity": (datetime.today() + timedelta(days=365)).strftime("%Y-%m-%d"),
        "Frequency": 1,
        "Notional": 100,
        "Price": "$95.965211",
        "Menu": DEFAULT_MENU,
    }
