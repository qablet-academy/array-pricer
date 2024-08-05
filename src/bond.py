from datetime import datetime
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
