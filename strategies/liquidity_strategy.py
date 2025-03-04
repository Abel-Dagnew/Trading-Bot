import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class LiquidityStrategy(BaseStrategy):
    def __init__(self, symbol, timeframe, risk_percentage=1.0):
        super().__init__(symbol, timeframe, risk_percentage)
        self.liquidity_levels = []
        self.order_blocks = []
        print(f"Initialized Liquidity Strategy for {symbol} on {timeframe}min timeframe")

    def identify_liquidity_levels(self, data: pd.DataFrame) -> list:
        """
        Identify potential liquidity levels (highs and lows)
        
        Args:
            data (pd.DataFrame): Historical price data
            
        Returns:
            list: List of liquidity levels
        """
        # Get previous highs and lows
        highs = data['high'].rolling(window=20).max()
        lows = data['low'].rolling(window=20).min()
        
        # Identify swing highs and lows
        swing_highs = []
        swing_lows = []
        
        for i in range(2, len(data)-2):
            # Swing high
            if data['high'].iloc[i] > data['high'].iloc[i-1] and \
               data['high'].iloc[i] > data['high'].iloc[i-2] and \
               data['high'].iloc[i] > data['high'].iloc[i+1] and \
               data['high'].iloc[i] > data['high'].iloc[i+2]:
                swing_highs.append((i, data['high'].iloc[i]))
            
            # Swing low
            if data['low'].iloc[i] < data['low'].iloc[i-1] and \
               data['low'].iloc[i] < data['low'].iloc[i-2] and \
               data['low'].iloc[i] < data['low'].iloc[i+1] and \
               data['low'].iloc[i] < data['low'].iloc[i+2]:
                swing_lows.append((i, data['low'].iloc[i]))
        
        return swing_highs, swing_lows

    def identify_order_blocks(self, data: pd.DataFrame) -> list:
        """
        Identify potential order blocks
        
        Args:
            data (pd.DataFrame): Historical price data
            
        Returns:
            list: List of order blocks
        """
        order_blocks = []
        
        for i in range(1, len(data)-1):
            # Bullish order block
            if data['close'].iloc[i] > data['open'].iloc[i] and \
               data['low'].iloc[i] < data['low'].iloc[i-1] and \
               data['low'].iloc[i] < data['low'].iloc[i+1]:
                order_blocks.append({
                    'type': 'bullish',
                    'index': i,
                    'high': data['high'].iloc[i],
                    'low': data['low'].iloc[i],
                    'close': data['close'].iloc[i]
                })
            
            # Bearish order block
            if data['close'].iloc[i] < data['open'].iloc[i] and \
               data['high'].iloc[i] > data['high'].iloc[i-1] and \
               data['high'].iloc[i] > data['high'].iloc[i+1]:
                order_blocks.append({
                    'type': 'bearish',
                    'index': i,
                    'high': data['high'].iloc[i],
                    'low': data['low'].iloc[i],
                    'close': data['close'].iloc[i]
                })
        
        return order_blocks

    def identify_fair_value_gaps(self, data: pd.DataFrame) -> list:
        """
        Identify Fair Value Gaps (FVG)
        
        Args:
            data (pd.DataFrame): Historical price data
            
        Returns:
            list: List of fair value gaps
        """
        fvgs = []
        
        for i in range(1, len(data)-1):
            # Bullish FVG
            if data['low'].iloc[i+1] > data['high'].iloc[i]:
                fvgs.append({
                    'type': 'bullish',
                    'index': i,
                    'high': data['high'].iloc[i],
                    'low': data['low'].iloc[i+1]
                })
            
            # Bearish FVG
            if data['high'].iloc[i+1] < data['low'].iloc[i]:
                fvgs.append({
                    'type': 'bearish',
                    'index': i,
                    'high': data['low'].iloc[i],
                    'low': data['high'].iloc[i+1]
                })
        
        return fvgs

    def generate_signals(self, data: pd.DataFrame) -> dict:
        """
        Generate trading signals based on liquidity and market structure
        
        Args:
            data (pd.DataFrame): Historical price data
            
        Returns:
            dict: Signal information
        """
        # Get current price
        current_price = data['close'].iloc[-1]
        
        # Identify liquidity levels
        swing_highs, swing_lows = self.identify_liquidity_levels(data)
        
        # Identify order blocks
        order_blocks = self.identify_order_blocks(data)
        
        # Identify fair value gaps
        fvgs = self.identify_fair_value_gaps(data)
        
        print("\nStrategy Analysis:")
        print(f"Current Price: {current_price:.5f}")
        print(f"Number of Swing Highs: {len(swing_highs)}")
        print(f"Number of Swing Lows: {len(swing_lows)}")
        print(f"Number of Order Blocks: {len(order_blocks)}")
        print(f"Number of FVGs: {len(fvgs)}")
        
        # Check for bullish setup
        if len(swing_lows) > 0 and len(order_blocks) > 0:
            last_swing_low = swing_lows[-1][1]
            last_bullish_ob = next((ob for ob in order_blocks if ob['type'] == 'bullish'), None)
            
            if last_bullish_ob and current_price > last_bullish_ob['high']:
                stop_loss = last_swing_low
                take_profit = current_price + (current_price - stop_loss) * 2  # 1:2 RR ratio
                
                print("\nSignal: BULLISH SETUP DETECTED!")
                print(f"Price above bullish order block")
                
                return {
                    'action': 'buy',
                    'price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'reason': 'Price above bullish order block'
                }
        
        # Check for bearish setup
        if len(swing_highs) > 0 and len(order_blocks) > 0:
            last_swing_high = swing_highs[-1][1]
            last_bearish_ob = next((ob for ob in order_blocks if ob['type'] == 'bearish'), None)
            
            if last_bearish_ob and current_price < last_bearish_ob['low']:
                stop_loss = last_swing_high
                take_profit = current_price - (stop_loss - current_price) * 2  # 1:2 RR ratio
                
                print("\nSignal: BEARISH SETUP DETECTED!")
                print(f"Price below bearish order block")
                
                return {
                    'action': 'sell',
                    'price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'reason': 'Price below bearish order block'
                }
        
        print("\nNo trading signals detected")
        return {
            'action': None,
            'price': current_price,
            'stop_loss': None,
            'take_profit': None,
            'reason': 'No signal'
        }

    def calculate_position_size(self, account_balance: float, stop_loss: float) -> float:
        """
        Calculate position size based on risk management rules
        
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