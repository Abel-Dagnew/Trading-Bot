import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class MACrossoverStrategy(BaseStrategy):
    def __init__(self, symbol, timeframe, fast_period=10, slow_period=20, risk_percentage=1.0):
        super().__init__(symbol, timeframe, risk_percentage)
        self.fast_period = fast_period
        self.slow_period = slow_period
        print(f"Initialized MA Crossover Strategy with {fast_period} and {slow_period} period MAs")

    def generate_signals(self, data: pd.DataFrame) -> dict:
        """
        Generate trading signals based on moving average crossover.
        
        Args:
            data (pd.DataFrame): Historical price data with 'close' column
            
        Returns:
            dict: Signal information
        """
        # Calculate moving averages
        data['fast_ma'] = data['close'].rolling(window=self.fast_period).mean()
        data['slow_ma'] = data['close'].rolling(window=self.slow_period).mean()
        
        # Get the last two rows for crossover detection
        last_row = data.iloc[-1]
        prev_row = data.iloc[-2]
        
        print(f"\nStrategy Analysis:")
        print(f"Fast MA ({self.fast_period}): {last_row['fast_ma']:.5f}")
        print(f"Slow MA ({self.slow_period}): {last_row['slow_ma']:.5f}")
        print(f"Current Price: {last_row['close']:.5f}")
        
        # Check for crossover
        if last_row['fast_ma'] > last_row['slow_ma'] and prev_row['fast_ma'] <= prev_row['slow_ma']:
            # Bullish crossover
            stop_loss = last_row['close'] * 0.99  # 1% below entry
            take_profit = last_row['close'] * 1.02  # 2% above entry
            
            print("\nSignal: BULLISH CROSSOVER DETECTED!")
            print(f"Fast MA crossed above Slow MA")
            
            return {
                'action': 'buy',
                'price': last_row['close'],
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'reason': 'Bullish MA crossover'
            }
            
        elif last_row['fast_ma'] < last_row['slow_ma'] and prev_row['fast_ma'] >= prev_row['slow_ma']:
            # Bearish crossover
            stop_loss = last_row['close'] * 1.01  # 1% above entry
            take_profit = last_row['close'] * 0.98  # 2% below entry
            
            print("\nSignal: BEARISH CROSSOVER DETECTED!")
            print(f"Fast MA crossed below Slow MA")
            
            return {
                'action': 'sell',
                'price': last_row['close'],
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'reason': 'Bearish MA crossover'
            }
        
        print("\nNo crossover signals detected")
        return {
            'action': None,
            'price': last_row['close'],
            'stop_loss': None,
            'take_profit': None,
            'reason': 'No signal'
        }

    def calculate_position_size(self, account_balance: float, stop_loss: float) -> float:
        """
        Calculate position size based on risk management rules.
        
        Args:
            account_balance (float): Current account balance
            stop_loss (float): Stop loss price
            
        Returns:
            float: Position size in lots
        """
        risk_amount = account_balance * (self.risk_percentage / 100)
        current_price = self.position['price'] if self.position else 0
        
        if current_price == 0 or stop_loss == 0:
            return 0
            
        # Calculate pip value (assuming standard lot size)
        pip_value = 0.0001  # For most forex pairs
        risk_pips = abs(current_price - stop_loss) / pip_value
        
        # Calculate position size (1 standard lot = 100,000 units)
        position_size = risk_amount / (risk_pips * 10)  # 10 USD per pip for standard lot
        
        # Round to nearest 0.01 lot
        return round(position_size, 2) 