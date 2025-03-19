import requests
import logging
from datetime import datetime

class AvaTradeWebTrader:
    def __init__(self):
        # Updated to use the correct WebTrader URL
        self.base_url = "https://webtrader7.avatrade.com"
        self.session = requests.Session()
        self.logged_in = False

    def login(self):
        """Login to AvaTrade WebTrader"""
        try:
            login_url = f"{self.base_url}/auth/login"
            
            # WebTrader login data
            data = {
                "username": "101490832",    # Your account number
                "password": "Abel3078@",    # Your password
                "accountType": "DEMO"       # DEMO account
            }
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0',
                'Origin': 'https://webtrader7.avatrade.com',
                'Referer': 'https://webtrader7.avatrade.com/login'
            }

            response = requests.post(login_url, json=data, headers=headers)
            
            if response.status_code == 200:
                token = response.json().get('token')
                if token:
                    self.session.headers.update({
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json',
                        'Origin': 'https://webtrader7.avatrade.com'
                    })
                    self.logged_in = True
                    logging.info("Successfully logged in to AvaTrade WebTrader")
                    return True
            
            logging.error(f"Login failed: {response.text}")
            return False
            
        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            return False

    def get_price(self, symbol='EURUSD'):
        """Get current price for a symbol"""
        try:
            price_url = f"{self.base_url}/prices/{symbol}"
            response = self.session.get(price_url)
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logging.error(f"Price fetch error: {str(e)}")
            return None

    def get_account_info(self):
        """Get account information"""
        try:
            account_url = f"{self.base_url}/account/info"
            response = self.session.get(account_url)
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logging.error(f"Account info error: {str(e)}")
            return None

    def place_order(self, symbol, direction, volume):
        """Place a market order"""
        try:
            order_url = f"{self.base_url}/trading/order"
            
            data = {
                "symbol": symbol,
                "type": "MARKET",
                "side": direction.upper(),
                "quantity": volume,
                "timeInForce": "GTC"
            }
            
            response = self.session.post(order_url, json=data)
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logging.error(f"Order placement error: {str(e)}")
            return None 