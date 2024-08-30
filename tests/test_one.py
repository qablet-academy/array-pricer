#from src.bond import create_default_bond
#from src.price import update_price
#from datetime import datetime, timedelta

#def test_simple():
   # data = [create_default_bond(index=1)]
    #update_price(data, rate_data=[{"Rate": 0.05, "Year": 0}, {"Rate": 0.05, "Year": 5}])
   # assert data[0]["Price"] == "$101.798925"

#def test_different_coupon_rate():
    #data = [create_default_bond(index=1)]
    #data[0]["Coupon"] = 5.0  # Set a higher coupon rate
    #update_price(data, rate_data=[{"Rate": 0.05, "Year": 0}, {"Rate": 0.05, "Year": 5}])
   # assert data[0]["Price"] == "$104.202272"  # Expected price with a 5% coupon rate

#def test_different_maturity():
    #data = [create_default_bond(index=1)]
    #data[0]["Maturity"] = (datetime.today() + timedelta(days=365 * 10)).strftime("%Y-%m-%d")  # 10 years maturity
    #update_price(data, rate_data=[{"Rate": 0.05, "Year": 0}, {"Rate": 0.05, "Year": 5}, {"Rate": 0.05, "Year": 10}])
    #assert data[0]["Price"] == "$125.051800"  # Expected price with 10-year maturity