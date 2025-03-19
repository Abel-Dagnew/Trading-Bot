import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import time
import logging
from dotenv import load_dotenv
import os

class MT5Connector:
    def __init__(self):
        self.connected = False
        # Your AvaTrade MT5 demo credentials
        self.login = 101490832
        self.password = "Abel3078@"
        self.server = "Ava-Demo 1-MT5"
        
    def connect(self):
        """Connect to MT5"""
        try:
            # Initialize MT5
            if not mt5.initialize():
                logging.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False
                
            # Login to MT5
            if not mt5.login(
                login=self.login,
                password=self.password, 
                server=self.server
            ):
                logging.error(f"MT5 login failed: {mt5.last_error()}")
                mt5.shutdown()
                return False
                
            self.connected = True
            account_info = mt5.account_info()
            logging.info(f"Successfully connected to MT5. Balance: ${account_info.balance}")
            return True
            
        except Exception as e:
            logging.error(f"Connection error: {str(e)}")
            return False

    def get_account_info(self):
        """Get account information"""
        if not self.connected:
            return None
            
        try:
            account_info = mt5.account_info()
            if account_info is None:
                logging.error(f"Failed to get account info: {mt5.last_error()}")
                return None
                
            return {
                'balance': account_info.balance,
                'equity': account_info.equity,
                'margin': account_info.margin,
                'free_margin': account_info.margin_free,
                'leverage': account_info.leverage
            }
        except Exception as e:
            logging.error(f"Account info error: {str(e)}")
            return None

    def get_symbol_info(self, symbol):
        """Get symbol information"""
        if not self.connected:
            return None
            
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                logging.error(f"Failed to get symbol info: {mt5.last_error()}")
                return None
                
            return {
                'bid': symbol_info.bid,
                'ask': symbol_info.ask,
                'spread': symbol_info.spread,
                'digits': symbol_info.digits,
                'volume_min': symbol_info.volume_min,
                'volume_step': symbol_info.volume_step
            }
        except Exception as e:
            logging.error(f"Symbol info error: {str(e)}")
            return None

    def place_order(self, symbol, order_type, volume, price=None, 
                   stop_loss=None, take_profit=None):
        """Place a trading order"""
        if not self.connected:
            return None
            
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return None
                
            point = symbol_info.point
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": float(volume),
                "type": mt5.ORDER_TYPE_BUY if order_type.upper() == 'BUY' else mt5.ORDER_TYPE_SELL,
                "price": price or (symbol_info.ask if order_type.upper() == 'BUY' else symbol_info.bid),
                "deviation": 20,
                "magic": 234000,
                "comment": "Python Trading Bot",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            if stop_loss:
                request["sl"] = stop_loss
            if take_profit:
                request["tp"] = take_profit
                
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logging.error(f"Order failed: {result.comment}")
                return None
                
            logging.info(f"Order placed successfully: {result.order}")
            return result.order
            
        except Exception as e:
            logging.error(f"Order placement error: {str(e)}")
            return None

    def get_positions(self):
        """Get open positions"""
        if not self.connected:
            return []
            
        try:
            positions = mt5.positions_get()
            if positions is None:
                logging.error(f"Failed to get positions: {mt5.last_error()}")
                return []
                
            return [{
                'ticket': pos.ticket,
                'symbol': pos.symbol,
                'type': 'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL',
                'volume': pos.volume,
                'price': pos.price_open,
                'profit': pos.profit
            } for pos in positions]
            
        except Exception as e:
            logging.error(f"Get positions error: {str(e)}")
            return []

    def close(self):
        """Disconnect from MT5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logging.info("Disconnected from MT5")
        
    def get_historical_data(self, symbol: str, timeframe: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get historical data from MT5"""
        if not self.connected:
            return None
            
        # Convert timeframe string to MT5 timeframe
        timeframe_map = {
            '1m': mt5.TIMEFRAME_M1,
            '5m': mt5.TIMEFRAME_M5,
            '15m': mt5.TIMEFRAME_M15,
            '1h': mt5.TIMEFRAME_H1,
            '4h': mt5.TIMEFRAME_H4,
            '1d': mt5.TIMEFRAME_D1
        }
        
        if timeframe not in timeframe_map:
            logging.error(f"Invalid timeframe: {timeframe}")
            return None
            
        # Get historical data
        rates = mt5.copy_rates_range(symbol, timeframe_map[timeframe], start_date, end_date)
        if rates is None:
            logging.error(f"Failed to get historical data: {mt5.last_error()}")
            return None
            
        # Convert to DataFrame
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        # Rename columns to match our strategy's expectations
        df = df.rename(columns={
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'tick_volume': 'volume'
        })
        
        return df
        
    def close_order(self, order_id: int) -> bool:
        """Close an existing order"""
        if not self.connected:
            return False
            
        # Get order details
        order = mt5.positions_get(ticket=order_id)
        if not order:
            logging.error(f"Failed to get order details: {mt5.last_error()}")
            return False
            
        order = order[0]
        
        # Prepare close request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": order.symbol,
            "volume": order.volume,
            "type": mt5.ORDER_TYPE_SELL if order.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            "position": order.ticket,
            "price": mt5.symbol_info_tick(order.symbol).bid if order.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(order.symbol).ask,
            "deviation": 20,
            "magic": 234000,
            "comment": "Python Trading Bot - Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Send close request
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logging.error(f"Failed to close order: {result.comment}")
            return False
            
        logging.info(f"Order closed successfully: {order_id}")
        return True 