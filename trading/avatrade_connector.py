import requests
import logging
from datetime import datetime
import json

class AvaTradeAPI:
    def __init__(self, demo=True):
        self.demo = demo
        # Official AvaTrade API endpoint
        self.base_url = "https://live.avatrade.com/api/v1" if not demo else "https://demo.avatrade.com/api/v1"
        self.session = requests.Session()
        self.token = None
        
    def login(self, username, password):
        """Login to AvaTrade demo account"""
        try:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            data = {
                'grant_type': 'password',
                'username': '101490832',  # Your demo account number
                'password': 'Abel3078@'   # Your demo account password
            }
            
            response = requests.post(
                f"{self.base_url}/authentication/login", 
                headers=headers,
                data=data
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data.get('access_token')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json'
                })
                logging.info("Successfully logged in to AvaTrade demo account")
                return True
            else:
                logging.error(f"Login failed: {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            return False

    def get_account_info(self):
        """Get real account information"""
        try:
            response = self.session.get(f"{self.base_url}/account/details")
            if response.status_code == 200:
                return response.json()
            logging.error(f"Failed to get account info: {response.text}")
            return None
        except Exception as e:
            logging.error(f"Account info error: {str(e)}")
            return None

    def place_order(self, symbol, direction, volume, stop_loss=None, take_profit=None):
        """Place a real market order"""
        try:
            data = {
                "instrumentName": symbol,
                "volume": volume,
                "side": direction.upper(),  # "BUY" or "SELL"
                "type": "MARKET",
                "timeInForce": "GTC"
            }
            
            if stop_loss:
                data["stopLoss"] = stop_loss
            if take_profit:
                data["takeProfit"] = take_profit

            response = self.session.post(f"{self.base_url}/trading/order", json=data)
            if response.status_code == 200:
                return response.json()
            logging.error(f"Order failed: {response.text}")
            return None
        except Exception as e:
            logging.error(f"Order error: {str(e)}")
            return None

    def get_positions(self):
        """Get real open positions"""
        try:
            response = self.session.get(f"{self.base_url}/trading/positions")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logging.error(f"Get positions error: {str(e)}")
            return []

    def get_instruments(self):
        """Get available trading instruments"""
        try:
            response = self.session.get(f"{self.base_url}/instruments")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logging.error(f"Get instruments error: {str(e)}")
            return []

    def get_market_price(self, symbol):
        """Get real-time market price"""
        try:
            response = self.session.get(f"{self.base_url}/market/prices/{symbol}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logging.error(f"Get market price error: {str(e)}")
            return None 