import pandas as pd
import numpy as np
from datetime import datetime, time
from .base_strategy import BaseStrategy

class ICTStrategy(BaseStrategy):
    def __init__(self, symbol, timeframe, risk_percentage=1.0):
        super().__init__(symbol, timeframe, risk_percentage)
        self.session_ranges = {
            'ny_midnight': {'high': None, 'low': None},
            'london': {'high': None, 'low': None},
            'ny': {'high': None, 'low': None}
        }
        print(f"Initialized ICT Strategy for {symbol} on {timeframe}min timeframe")

    def get_current_session(self) -> str:
        """Determine the current trading session based on time"""
        current_time = datetime.now().time()
        
        # NY Midnight: 12:00 AM - 03:00 AM EST
        if time(0, 0) <= current_time < time(3, 0):
            return 'ny_midnight'
        # London: 03:00 AM - 08:00 AM EST
        elif time(3, 0) <= current_time < time(8, 0):
            return 'london'
        # NY: 08:00 AM - 12:00 PM EST
        elif time(8, 0) <= current_time < time(12, 0):
            return 'ny'
        else:
            return 'closed'

    def update_session_range(self, session: str, data: pd.DataFrame):
        """Update the high and low for the current session"""
        if session in self.session_ranges:
            self.session_ranges[session]['high'] = data['high'].max()
            self.session_ranges[session]['low'] = data['low'].min()
            print(f"\nUpdated {session} session range:")
            print(f"High: {self.session_ranges[session]['high']:.5f}")
            print(f"Low: {self.session_ranges[session]['low']:.5f}")

    def identify_liquidity_sweep(self, data: pd.DataFrame, session: str) -> bool:
        """Check if price has swept the session's liquidity"""
        if session not in self.session_ranges:
            return False
            
        current_price = data['close'].iloc[-1]
        session_high = self.session_ranges[session]['high']
        session_low = self.session_ranges[session]['low']
        
        if session_high and session_low:
            # Check for high sweep
            if current_price > session_high:
                print(f"\nHigh liquidity sweep detected at {current_price:.5f}")
                return True
            # Check for low sweep
            elif current_price < session_low:
                print(f"\nLow liquidity sweep detected at {current_price:.5f}")
                return True
        
        return False

    def identify_market_structure_shift(self, data: pd.DataFrame) -> dict:
        """Identify market structure shift using ICT methodology"""
        # Get last 20 candles
        recent_data = data.tail(20)
        
        # Calculate swing highs and lows
        swing_highs = []
        swing_lows = []
        
        for i in range(2, len(recent_data)-2):
            # Swing high
            if recent_data['high'].iloc[i] > recent_data['high'].iloc[i-1] and \
               recent_data['high'].iloc[i] > recent_data['high'].iloc[i-2] and \
               recent_data['high'].iloc[i] > recent_data['high'].iloc[i+1] and \
               recent_data['high'].iloc[i] > recent_data['high'].iloc[i+2]:
                swing_highs.append((i, recent_data['high'].iloc[i]))
            
            # Swing low
            if recent_data['low'].iloc[i] < recent_data['low'].iloc[i-1] and \
               recent_data['low'].iloc[i] < recent_data['low'].iloc[i-2] and \
               recent_data['low'].iloc[i] < recent_data['low'].iloc[i+1] and \
               recent_data['low'].iloc[i] < recent_data['low'].iloc[i+2]:
                swing_lows.append((i, recent_data['low'].iloc[i]))
        
        # Check for structure shift
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            # Bearish shift
            if swing_highs[-1][1] < swing_highs[-2][1] and swing_lows[-1][1] < swing_lows[-2][1]:
                return {'type': 'bearish', 'high': swing_highs[-1][1], 'low': swing_lows[-1][1]}
            # Bullish shift
            elif swing_highs[-1][1] > swing_highs[-2][1] and swing_lows[-1][1] > swing_lows[-2][1]:
                return {'type': 'bullish', 'high': swing_highs[-1][1], 'low': swing_lows[-1][1]}
        
        return None

    def identify_pd_array(self, data: pd.DataFrame, structure_shift: dict) -> dict:
        """Identify Premium/Discount array (Order Blocks, FVGs, etc.)"""
        if not structure_shift:
            return None
            
        current_price = data['close'].iloc[-1]
        
        # Look for order blocks
        order_blocks = []
        for i in range(1, len(data)-1):
            if structure_shift['type'] == 'bullish':
                # Bullish order block
                if data['close'].iloc[i] > data['open'].iloc[i] and \
                   data['low'].iloc[i] < data['low'].iloc[i-1] and \
                   data['low'].iloc[i] < data['low'].iloc[i+1]:
                    order_blocks.append({
                        'type': 'bullish',
                        'high': data['high'].iloc[i],
                        'low': data['low'].iloc[i]
                    })
            else:
                # Bearish order block
                if data['close'].iloc[i] < data['open'].iloc[i] and \
                   data['high'].iloc[i] > data['high'].iloc[i-1] and \
                   data['high'].iloc[i] > data['high'].iloc[i+1]:
                    order_blocks.append({
                        'type': 'bearish',
                        'high': data['high'].iloc[i],
                        'low': data['low'].iloc[i]
                    })
        
        # Look for Fair Value Gaps
        fvgs = []
        for i in range(1, len(data)-1):
            if structure_shift['type'] == 'bullish':
                # Bullish FVG
                if data['low'].iloc[i+1] > data['high'].iloc[i]:
                    fvgs.append({
                        'type': 'bullish',
                        'high': data['high'].iloc[i],
                        'low': data['low'].iloc[i+1]
                    })
            else:
                # Bearish FVG
                if data['high'].iloc[i+1] < data['low'].iloc[i]:
                    fvgs.append({
                        'type': 'bearish',
                        'high': data['low'].iloc[i],
                        'low': data['high'].iloc[i+1]
                    })
        
        return {
            'order_blocks': order_blocks,
            'fvgs': fvgs,
            'current_price': current_price
        }

    def generate_signals(self, data: pd.DataFrame) -> dict:
        """Generate trading signals based on ICT methodology"""
        current_session = self.get_current_session()
        print(f"\nCurrent Session: {current_session}")
        
        # Update session range
        self.update_session_range(current_session, data)
        
        # Check for liquidity sweep
        if self.identify_liquidity_sweep(data, current_session):
            # Look for market structure shift
            structure_shift = self.identify_market_structure_shift(data)
            
            if structure_shift:
                print(f"\nMarket Structure Shift Detected: {structure_shift['type']}")
                
                # Look for PD array
                pd_array = self.identify_pd_array(data, structure_shift)
                
                if pd_array:
                    current_price = pd_array['current_price']
                    
                    # Check for trade setup
                    if structure_shift['type'] == 'bullish':
                        # Look for bullish setup
                        for ob in pd_array['order_blocks']:
                            if ob['type'] == 'bullish' and current_price > ob['high']:
                                stop_loss = structure_shift['low']
                                take_profit = current_price + (current_price - stop_loss) * 3  # 1:3 RR ratio
                                
                                print("\nSignal: BULLISH SETUP DETECTED!")
                                print(f"Price above bullish order block")
                                
                                return {
                                    'action': 'buy',
                                    'price': current_price,
                                    'stop_loss': stop_loss,
                                    'take_profit': take_profit,
                                    'reason': 'ICT Bullish Setup'
                                }
                    
                    else:
                        # Look for bearish setup
                        for ob in pd_array['order_blocks']:
                            if ob['type'] == 'bearish' and current_price < ob['low']:
                                stop_loss = structure_shift['high']
                                take_profit = current_price - (stop_loss - current_price) * 3  # 1:3 RR ratio
                                
                                print("\nSignal: BEARISH SETUP DETECTED!")
                                print(f"Price below bearish order block")
                                
                                return {
                                    'action': 'sell',
                                    'price': current_price,
                                    'stop_loss': stop_loss,
                                    'take_profit': take_profit,
                                    'reason': 'ICT Bearish Setup'
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