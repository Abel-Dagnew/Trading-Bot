import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import logging
import time
from datetime import datetime
import ta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ForexTradingBot:
    def __init__(self, symbols=None, lot_size=0.2, status_callback=None):
        self.symbols = symbols or ["GOLD", "EURUSD", "USDJPY", "GBPUSD", "USDCAD", "USDCHF", "AUDUSD", "NZDUSD"]
        self.lot_size = lot_size
        self.status_callback = status_callback
        self.recent_trades = []
        
        if not mt5.initialize():
            logging.error("MT5 initialization failed")
            raise Exception("MT5 initialization failed")
            
        if not mt5.login(101490832, password="Abel3078@", server="Ava-Demo 1-MT5"):
            logging.error("MT5 login failed")
            mt5.shutdown()
            raise Exception("MT5 login failed")
            
        logging.info("MT5 connection established successfully")

    def get_signal(self, symbol):
        """ICT strategy with 15M, 5M, 1M timeframes"""
        try:
            # Get multiple timeframe data
            m15_data = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)  # Higher timeframe trend
            m5_data = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 100)    # Order blocks
            m1_data = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 100)    # Entry and FVG
            
            if m15_data is None or m5_data is None or m1_data is None:
                logging.error(f"Unable to get data for {symbol}")
                return None
                
            # Convert to DataFrames
            m15_df = pd.DataFrame(m15_data)
            m5_df = pd.DataFrame(m5_data)
            m1_df = pd.DataFrame(m1_data)
            
            # 1. Market Structure Analysis (15M)
            def analyze_structure(df):
                df['high_prev'] = df['high'].shift(1)
                df['low_prev'] = df['low'].shift(1)
                df['higher_high'] = df['high'] > df['high'].rolling(5).max()
                df['lower_low'] = df['low'] < df['low'].rolling(5).min()
                
                # Add trend identification
                df['ema_20'] = df['close'].ewm(span=20).mean()
                df['ema_50'] = df['close'].ewm(span=50).mean()
                df['trend_up'] = df['ema_20'] > df['ema_50']
                df['trend_down'] = df['ema_20'] < df['ema_50']
                return df
                
            # 2. Order Blocks (5M)
            def find_order_blocks(df):
                df['body_size'] = abs(df['close'] - df['open'])
                df['upper_wick'] = df.apply(lambda x: max(x['high'] - x['close'], x['high'] - x['open']), axis=1)
                df['lower_wick'] = df.apply(lambda x: min(x['close'] - x['low'], x['open'] - x['low']), axis=1)
                
                # Strong candle criteria
                df['is_strong_bull'] = (
                    (df['close'] > df['open']) & 
                    (df['body_size'] > df['body_size'].rolling(10).mean()) &
                    (df['lower_wick'] < df['body_size'] * 0.5)
                )
                df['is_strong_bear'] = (
                    (df['close'] < df['open']) & 
                    (df['body_size'] > df['body_size'].rolling(10).mean()) &
                    (df['upper_wick'] < df['body_size'] * 0.5)
                )
                
                # Order block identification
                df['bull_ob'] = df['is_strong_bull'].shift(1) & (df['low'].shift(1) > df['high'])
                df['bear_ob'] = df['is_strong_bear'].shift(1) & (df['high'].shift(1) < df['low'])
                return df
                
            # 3. Fair Value Gaps and Entry Precision (1M)
            def find_fvg_and_entry(df):
                # Fair Value Gaps
                df['bull_fvg'] = (df['low'].shift(1) > df['high'].shift(-1))
                df['bear_fvg'] = (df['high'].shift(1) < df['low'].shift(-1))
                
                # Entry precision with RSI
                df['rsi'] = ta.RSI(df['close'], timeperiod=14)
                df['oversold'] = df['rsi'] < 30
                df['overbought'] = df['rsi'] > 70
                return df
            
            # Apply analysis to all timeframes
            m15_df = analyze_structure(m15_df)
            m5_df = find_order_blocks(m5_df)
            m1_df = find_fvg_and_entry(m1_df)
            
            # Check for buy setup
            def check_buy_setup():
                # 15M trend must be up
                m15_uptrend = (
                    m15_df['trend_up'].iloc[-1] and 
                    m15_df['higher_high'].iloc[-3:].any()
                )
                
                # 5M order block present
                m5_bull_ob = m5_df['bull_ob'].iloc[-5:].any()
                
                # 1M entry conditions
                m1_entry_valid = (
                    m1_df['bull_fvg'].iloc[-3:].any() and
                    m1_df['oversold'].iloc[-1]
                )
                
                return m15_uptrend and m5_bull_ob and m1_entry_valid
                
            # Check for sell setup
            def check_sell_setup():
                # 15M trend must be down
                m15_downtrend = (
                    m15_df['trend_down'].iloc[-1] and 
                    m15_df['lower_low'].iloc[-3:].any()
                )
                
                # 5M order block present
                m5_bear_ob = m5_df['bear_ob'].iloc[-5:].any()
                
                # 1M entry conditions
                m1_entry_valid = (
                    m1_df['bear_fvg'].iloc[-3:].any() and
                    m1_df['overbought'].iloc[-1]
                )
                
                return m15_downtrend and m5_bear_ob and m1_entry_valid
            
            # Generate trading signal
            current_price = m1_df['close'].iloc[-1]
            
            if check_buy_setup():
                logging.info(f"ICT Buy Signal for {symbol}: 15M trend + 5M OB + 1M FVG")
                return {
                    'action': 'BUY',
                    'current_price': current_price,
                    'reason': 'ICT Buy Setup: 15M trend + 5M OB + 1M FVG'
                }
            elif check_sell_setup():
                logging.info(f"ICT Sell Signal for {symbol}: 15M trend + 5M OB + 1M FVG")
                return {
                    'action': 'SELL',
                    'current_price': current_price,
                    'reason': 'ICT Sell Setup: 15M trend + 5M OB + 1M FVG'
                }
            
            return None
            
        except Exception as e:
            logging.error(f"Error in ICT analysis for {symbol}: {str(e)}")
            return None

    def place_order(self, symbol, order_type):
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return None
                
            price = symbol_info.ask if order_type == 'BUY' else symbol_info.bid
            point = symbol_info.point
            
            if symbol == "GOLD":
                sl_points = 150
                tp_points = 300
            else:
                sl_points = 30
                tp_points = 60
                
            if order_type == 'BUY':
                sl = price - (sl_points * point)
                tp = price + (tp_points * point)
            else:
                sl = price + (sl_points * point)
                tp = price - (tp_points * point)
                
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": self.lot_size,
                "type": mt5.ORDER_TYPE_BUY if order_type == 'BUY' else mt5.ORDER_TYPE_SELL,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": 234000,
                "comment": "python",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                return result.order
            return None
            
        except Exception as e:
            logging.error(f"Error placing order for {symbol}: {str(e)}")
            return None

    def run(self):
        """Main bot loop with 30-second check interval"""
        logging.info("Starting trading with ICT strategy...")
        
        try:
            while True:
                account_info = mt5.account_info()
                if account_info:
                    logging.info(f"Balance: ${account_info.balance}")
                
                for symbol in self.symbols:
                    try:
                        positions = mt5.positions_get(symbol=symbol)
                        if not positions:  # Only trade if no position exists
                            signal = self.get_signal(symbol)
                            
                            if signal:
                                ticket = self.place_order(
                                    symbol=symbol,
                                    order_type=signal['action']
                                )
                                
                                if ticket:
                                    self.recent_trades.append({
                                        'time': datetime.now(),
                                        'ticket': ticket,
                                        'symbol': symbol,
                                        'type': signal['action'],
                                        'reason': signal['reason']
                                    })
                                    
                    except Exception as e:
                        logging.error(f"Error processing {symbol}: {str(e)}")
                        continue
                
                # Update status
                if self.status_callback:
                    self.status_callback({
                        'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'account_balance': account_info.balance if account_info else 0,
                        'recent_trades': self.recent_trades[-20:],
                        'mode': 'Live Trading'
                    })
                
                time.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            logging.info("Bot stopped by user")
        except Exception as e:
            logging.error(f"Fatal error: {str(e)}")
        finally:
            self.close()

    def close(self):
        mt5.shutdown()
        logging.info("Bot shutdown complete")

# This line is important - it makes the class available for import
if __name__ != "__main__":
    __all__ = ['ForexTradingBot'] 