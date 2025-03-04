import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
import os
from strategies.base_strategy import BaseStrategy
import logging
from trading.mt5_connector import MT5Connector
from strategies.ict_combined_strategy import ICTCombinedStrategy

class TradingBot:
    def __init__(self, symbol: str, timeframe: str, risk_percentage: float = 1.0):
        """Initialize trading bot"""
        # Load environment variables
        load_dotenv()
        
        # Initialize MT5 connector
        self.mt5 = MT5Connector(
            login=int(os.getenv('MT5_LOGIN')),
            password=os.getenv('MT5_PASSWORD'),
            server=os.getenv('MT5_SERVER')
        )
        
        # Initialize strategy
        self.strategy = ICTCombinedStrategy(
            symbol=symbol,
            timeframe=timeframe,
            risk_percentage=risk_percentage
        )
        
        # Trading parameters
        self.symbol = symbol
        self.timeframe = timeframe
        self.risk_percentage = risk_percentage
        self.last_bar_time = None
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            filename='trading_bot.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def connect(self) -> bool:
        """Connect to MetaTrader 5"""
        return self.mt5.connect()
        
    def disconnect(self):
        """Disconnect from MetaTrader 5"""
        self.mt5.disconnect()
        
    def get_latest_data(self) -> pd.DataFrame:
        """Get latest market data"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)  # Get last 24 hours of data
        
        data = self.mt5.get_historical_data(
            self.symbol,
            self.timeframe,
            start_date,
            end_date
        )
        
        if data is None or data.empty:
            logging.error("Failed to get market data")
            return None
            
        return data
        
    def check_and_update_positions(self, current_price: float):
        """Check and update existing positions"""
        positions = self.mt5.get_open_positions()
        
        for position in positions:
            # Check if stop loss or take profit is hit
            if position.type == mt5.POSITION_TYPE_BUY:
                if current_price <= position.sl or current_price >= position.tp:
                    self.mt5.close_order(position.ticket)
            else:  # SELL position
                if current_price >= position.sl or current_price <= position.tp:
                    self.mt5.close_order(position.ticket)
                    
    def run(self):
        """Main trading loop"""
        if not self.connect():
            logging.error("Failed to connect to MetaTrader 5")
            return
            
        logging.info(f"Starting trading bot for {self.symbol} on {self.timeframe} timeframe")
        
        while True:
            try:
                # Get latest market data
                data = self.get_latest_data()
                if data is None:
                    time.sleep(60)  # Wait 1 minute before retrying
                    continue
                    
                # Check if we have a new bar
                current_bar_time = data.index[-1]
                if self.last_bar_time == current_bar_time:
                    time.sleep(1)  # Wait 1 second before checking again
                    continue
                    
                self.last_bar_time = current_bar_time
                
                # Get current price
                current_price = data['close'].iloc[-1]
                
                # Check and update existing positions
                self.check_and_update_positions(current_price)
                
                # Generate trading signals
                signal = self.strategy.analyze(data)
                
                if signal:
                    # Get account info for position sizing
                    account_info = self.mt5.get_account_info()
                    if account_info is None:
                        continue
                        
                    # Calculate position size
                    position_size = self.strategy.calculate_position_size(
                        account_info['balance'],
                        signal['stop_loss_dollars']
                    )
                    
                    # Place order
                    order_id = self.mt5.place_order(
                        symbol=self.symbol,
                        order_type=signal['action'],
                        volume=position_size,
                        stop_loss=signal['stop_loss'],
                        take_profit=signal['take_profit']
                    )
                    
                    if order_id:
                        logging.info(f"Placed {signal['action']} order: {order_id}")
                        
                # Wait for next iteration
                time.sleep(1)
                
            except Exception as e:
                logging.error(f"Error in main loop: {str(e)}")
                time.sleep(60)  # Wait 1 minute before retrying
                
def main():
    # Initialize trading bot
    bot = TradingBot(
        symbol='XAUUSD',  # Gold symbol in MT5
        timeframe='1m',
        risk_percentage=1.0
    )
    
    try:
        # Run the bot
        bot.run()
    except KeyboardInterrupt:
        logging.info("Trading bot stopped by user")
    finally:
        bot.disconnect()
        
if __name__ == "__main__":
    main() 