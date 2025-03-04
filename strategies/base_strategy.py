from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from datetime import datetime

class BaseStrategy(ABC):
    def __init__(self, symbol, timeframe, risk_percentage=1.0):
        self.symbol = symbol
        self.timeframe = timeframe
        self.risk_percentage = risk_percentage
        self.position = None
        self.last_signal = None
        self.last_signal_time = None
        
    @abstractmethod
    def analyze(self, data: pd.DataFrame) -> dict:
        """Analyze market data and return trading signals"""
        pass
    
    @abstractmethod
    def calculate_position_size(self, account_balance: float, stop_loss_pips: float) -> float:
        """Calculate position size based on risk management rules"""
        pass
    
    def get_daily_bias(self, data: pd.DataFrame) -> str:
        """Determine daily market bias"""
        # Create a copy of the data to avoid SettingWithCopyWarning
        daily_data = data.copy()
        daily_data['date'] = daily_data.index.date
        daily_open = daily_data.groupby('date')['open'].first()
        daily_close = daily_data.groupby('date')['close'].last()
        
        # Compare current day's open with previous day's close
        daily_data['prev_close'] = daily_close.shift(1)
        daily_data['bias'] = np.where(daily_data['open'] > daily_data['prev_close'], 'bullish', 'bearish')
        
        return daily_data['bias'].iloc[-1]
    
    def identify_liquidity_levels(self, data: pd.DataFrame) -> dict:
        """Identify key liquidity levels"""
        # Create a copy of the data to avoid SettingWithCopyWarning
        df = data.copy()
        
        # Identify swing highs and lows
        df['swing_high'] = (df['high'] > df['high'].shift(1)) & (df['high'] > df['high'].shift(-1))
        df['swing_low'] = (df['low'] < df['low'].shift(1)) & (df['low'] < df['low'].shift(-1))
        
        # Get recent swing points
        recent_highs = df[df['swing_high']]['high'].tail(5).tolist()
        recent_lows = df[df['swing_low']]['low'].tail(5).tolist()
        
        return {
            'recent_highs': recent_highs,
            'recent_lows': recent_lows
        }
    
    def identify_fair_value_gaps(self, data: pd.DataFrame) -> list:
        """Identify fair value gaps"""
        # Create a copy of the data to avoid SettingWithCopyWarning
        df = data.copy()
        
        fvgs = []
        for i in range(2, len(df)):
            # Bullish FVG
            if df['high'].iloc[i-2] > df['low'].iloc[i]:
                fvgs.append({
                    'type': 'bullish',
                    'high': df['high'].iloc[i-2],
                    'low': df['low'].iloc[i],
                    'time': df.index[i]
                })
                
            # Bearish FVG
            if df['low'].iloc[i-2] < df['high'].iloc[i]:
                fvgs.append({
                    'type': 'bearish',
                    'high': df['high'].iloc[i],
                    'low': df['low'].iloc[i-2],
                    'time': df.index[i]
                })
                
        return fvgs
    
    def identify_order_blocks(self, data: pd.DataFrame) -> list:
        """Identify order blocks"""
        # Create a copy of the data to avoid SettingWithCopyWarning
        df = data.copy()
        
        order_blocks = []
        for i in range(1, len(df)-1):  # Stop one candle before the end
            # Bullish order block
            if (df['close'].iloc[i] > df['open'].iloc[i] and 
                df['close'].iloc[i+1] < df['open'].iloc[i+1]):
                order_blocks.append({
                    'type': 'bullish',
                    'high': df['high'].iloc[i],
                    'low': df['low'].iloc[i],
                    'time': df.index[i]
                })
                
            # Bearish order block
            if (df['close'].iloc[i] < df['open'].iloc[i] and 
                df['close'].iloc[i+1] > df['open'].iloc[i+1]):
                order_blocks.append({
                    'type': 'bearish',
                    'high': df['high'].iloc[i],
                    'low': df['low'].iloc[i],
                    'time': df.index[i]
                })
                
        return order_blocks
    
    def identify_breaker_blocks(self, data: pd.DataFrame) -> list:
        """Identify breaker blocks"""
        # Create a copy of the data to avoid SettingWithCopyWarning
        df = data.copy()
        
        breaker_blocks = []
        order_blocks = self.identify_order_blocks(df)
        
        for i in range(1, len(df)):
            for ob in order_blocks:
                # Bullish breaker block
                if (ob['type'] == 'bearish' and 
                    df['close'].iloc[i] > ob['high']):
                    breaker_blocks.append({
                        'type': 'bullish',
                        'high': ob['high'],
                        'low': ob['low'],
                        'time': df.index[i]
                    })
                    
                # Bearish breaker block
                if (ob['type'] == 'bullish' and 
                    df['close'].iloc[i] < ob['low']):
                    breaker_blocks.append({
                        'type': 'bearish',
                        'high': ob['high'],
                        'low': ob['low'],
                        'time': df.index[i]
                    })
                    
        return breaker_blocks

    def update_position(self, current_price: float):
        """
        Update the current position status.
        
        Args:
            current_price (float): Current market price
        """
        if self.position:
            if current_price >= self.position['take_profit']:
                self.position = None
                self.last_signal = 'close_tp'
            elif current_price <= self.position['stop_loss']:
                self.position = None
                self.last_signal = 'close_sl'

    def get_position(self) -> dict:
        """
        Get the current position information.
        
        Returns:
            dict: Current position information or None if no position
        """
        return self.position

    def get_last_signal(self) -> str:
        """
        Get the last trading signal.
        
        Returns:
            str: Last signal information
        """
        return self.last_signal 