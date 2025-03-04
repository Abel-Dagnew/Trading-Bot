import pandas as pd
import numpy as np
from datetime import datetime, time
from .base_strategy import BaseStrategy

class AMDStrategy(BaseStrategy):
    def __init__(self, symbol, timeframe, risk_percentage=1.0):
        super().__init__(symbol, timeframe, risk_percentage)
        self.daily_bias = None
        self.accumulation_range = {'high': None, 'low': None}
        self.manipulation_phase = False
        self.distribution_phase = False
        print(f"Initialized AMD Strategy for {symbol} on {timeframe}min timeframe")

    def determine_daily_bias(self, data: pd.DataFrame) -> str:
        """Determine the daily bias based on higher timeframe analysis"""
        # Get daily data
        daily_data = data.resample('D').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        }).dropna()
        
        if len(daily_data) < 2:
            return None
            
        # Compare current day's open with previous day's close
        current_open = daily_data['open'].iloc[-1]
        prev_close = daily_data['close'].iloc[-2]
        
        if current_open > prev_close:
            return 'bullish'
        else:
            return 'bearish'

    def identify_accumulation_phase(self, data: pd.DataFrame) -> bool:
        """Identify if price is in accumulation phase"""
        # Get recent price action
        recent_data = data.tail(20)
        
        # Calculate price range
        price_range = recent_data['high'].max() - recent_data['low'].min()
        avg_range = price_range / 20
        
        # Check if price is ranging (low volatility)
        if price_range < avg_range * 1.5:
            self.accumulation_range = {
                'high': recent_data['high'].max(),
                'low': recent_data['low'].min()
            }
            print("\nAccumulation Phase Detected:")
            print(f"Range High: {self.accumulation_range['high']:.5f}")
            print(f"Range Low: {self.accumulation_range['low']:.5f}")
            return True
            
        return False

    def identify_manipulation_phase(self, data: pd.DataFrame) -> bool:
        """Identify if price is in manipulation phase"""
        if not self.accumulation_range['high'] or not self.accumulation_range['low']:
            return False
            
        current_price = data['close'].iloc[-1]
        
        # Check for false breakout
        if self.daily_bias == 'bullish':
            # Bearish manipulation (price breaks below accumulation low)
            if current_price < self.accumulation_range['low']:
                print("\nManipulation Phase Detected (Bearish)")
                self.manipulation_phase = True
                return True
        else:
            # Bullish manipulation (price breaks above accumulation high)
            if current_price > self.accumulation_range['high']:
                print("\nManipulation Phase Detected (Bullish)")
                self.manipulation_phase = True
                return True
                
        return False

    def identify_distribution_phase(self, data: pd.DataFrame) -> bool:
        """Identify if price is in distribution phase"""
        if not self.manipulation_phase:
            return False
            
        current_price = data['close'].iloc[-1]
        recent_data = data.tail(10)
        
        if self.daily_bias == 'bullish':
            # Price should be below accumulation low and showing bullish momentum
            if current_price < self.accumulation_range['low'] and \
               recent_data['close'].iloc[-1] > recent_data['open'].iloc[-1]:
                print("\nDistribution Phase Detected (Bullish)")
                self.distribution_phase = True
                return True
        else:
            # Price should be above accumulation high and showing bearish momentum
            if current_price > self.accumulation_range['high'] and \
               recent_data['close'].iloc[-1] < recent_data['open'].iloc[-1]:
                print("\nDistribution Phase Detected (Bearish)")
                self.distribution_phase = True
                return True
                
        return False

    def generate_signals(self, data: pd.DataFrame) -> dict:
        """Generate trading signals based on AMD methodology"""
        # Update daily bias
        self.daily_bias = self.determine_daily_bias(data)
        print(f"\nDaily Bias: {self.daily_bias}")
        
        # Check for accumulation phase
        if self.identify_accumulation_phase(data):
            return {
                'action': None,
                'price': data['close'].iloc[-1],
                'stop_loss': None,
                'take_profit': None,
                'reason': 'Accumulation Phase'
            }
            
        # Check for manipulation phase
        if self.identify_manipulation_phase(data):
            return {
                'action': None,
                'price': data['close'].iloc[-1],
                'stop_loss': None,
                'take_profit': None,
                'reason': 'Manipulation Phase'
            }
            
        # Check for distribution phase
        if self.identify_distribution_phase(data):
            current_price = data['close'].iloc[-1]
            
            if self.daily_bias == 'bullish':
                # Enter long position
                stop_loss = data['low'].iloc[-1]
                take_profit = current_price + (current_price - stop_loss) * 3  # 1:3 RR ratio
                
                print("\nSignal: BULLISH DISTRIBUTION PHASE!")
                print(f"Entering long position at {current_price:.5f}")
                
                return {
                    'action': 'buy',
                    'price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'reason': 'Bullish Distribution Phase'
                }
            else:
                # Enter short position
                stop_loss = data['high'].iloc[-1]
                take_profit = current_price - (stop_loss - current_price) * 3  # 1:3 RR ratio
                
                print("\nSignal: BEARISH DISTRIBUTION PHASE!")
                print(f"Entering short position at {current_price:.5f}")
                
                return {
                    'action': 'sell',
                    'price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'reason': 'Bearish Distribution Phase'
                }
        
        print("\nNo trading signals detected")
        return {
            'action': None,
            'price': data['close'].iloc[-1],
            'stop_loss': None,
            'take_profit': None,
            'reason': 'No signal'
        }

    def calculate_position_size(self, account_balance: float, stop_loss: float) -> float:
        """Calculate position size based on risk management rules"""
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