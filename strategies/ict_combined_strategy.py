from .base_strategy import BaseStrategy
import pandas as pd
import numpy as np
from datetime import datetime

class ICTCombinedStrategy(BaseStrategy):
    def __init__(self, symbol: str, timeframe: str, risk_percentage: float = 1.0):
        super().__init__(symbol, timeframe, risk_percentage)
        self.min_score_threshold = 65  # Lower threshold for gold's higher volatility
        self.min_risk_reward = 1.5  # Higher risk-reward for gold's larger moves
        self.max_daily_trades = 8  # Moderate number of trades for gold
        self.trades_today = 0
        self.last_trade_time = None
        self.price_data = []
        self.current_price = None
        
    def calculate_volatility(self, data: pd.DataFrame) -> float:
        """Calculate current market volatility"""
        returns = data['close'].pct_change()
        return returns.std() * np.sqrt(252)  # Annualized volatility
        
    def calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        high = data['high']
        low = data['low']
        close = data['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr.iloc[-1]
        
    def identify_strong_trend(self, data: pd.DataFrame) -> str:
        """Identify strong trend using multiple timeframes"""
        # Calculate EMAs with periods adjusted for gold
        ema20 = data['close'].ewm(span=20, adjust=False).mean()
        ema50 = data['close'].ewm(span=50, adjust=False).mean()
        ema100 = data['close'].ewm(span=100, adjust=False).mean()
        
        # Current values
        current_price = data['close'].iloc[-1]
        current_ema20 = ema20.iloc[-1]
        current_ema50 = ema50.iloc[-1]
        current_ema100 = ema100.iloc[-1]
        
        # Strong uptrend
        if (current_price > current_ema20 > current_ema50 > current_ema100):
            return 'strong_bullish'
        # Strong downtrend
        elif (current_price < current_ema20 < current_ema50 < current_ema100):
            return 'strong_bearish'
        # No strong trend
        return 'neutral'
        
    def identify_mitigation_blocks(self, data: pd.DataFrame) -> list:
        """Identify Mitigation Blocks (Reversal Patterns)"""
        # Create a copy of the data to avoid SettingWithCopyWarning
        df = data.copy()
        
        mitigation_blocks = []
        
        for i in range(2, len(df)-1):
            # Bearish Mitigation Block
            if (df['high'].iloc[i] < df['high'].iloc[i-1] and  # Failed to make higher high
                df['low'].iloc[i] < df['low'].iloc[i-2]):  # Broke previous higher low
                mitigation_blocks.append({
                    'type': 'bearish',
                    'high': df['high'].iloc[i],
                    'low': df['low'].iloc[i],
                    'time': df.index[i]
                })
            
            # Bullish Mitigation Block
            if (df['low'].iloc[i] > df['low'].iloc[i-1] and  # Failed to make lower low
                df['high'].iloc[i] > df['high'].iloc[i-2]):  # Broke previous lower high
                mitigation_blocks.append({
                    'type': 'bullish',
                    'high': df['high'].iloc[i],
                    'low': df['low'].iloc[i],
                    'time': df.index[i]
                })
        
        return mitigation_blocks
    
    def identify_market_structure_shift(self, data: pd.DataFrame) -> list:
        """Identify Market Structure Shift (MSS)"""
        # Create a copy of the data to avoid SettingWithCopyWarning
        df = data.copy()
        
        mss_signals = []
        
        for i in range(2, len(df)-1):
            # Bullish MSS
            if (df['low'].iloc[i] > df['low'].iloc[i-1] and  # Higher low
                df['low'].iloc[i] > df['low'].iloc[i-2] and  # Higher low
                df['close'].iloc[i] > df['high'].iloc[i-1]):  # Closes above previous high
                mss_signals.append({
                    'type': 'bullish',
                    'price': df['close'].iloc[i],
                    'time': df.index[i]
                })
            
            # Bearish MSS
            if (df['high'].iloc[i] < df['high'].iloc[i-1] and  # Lower high
                df['high'].iloc[i] < df['high'].iloc[i-2] and  # Lower high
                df['close'].iloc[i] < df['low'].iloc[i-1]):  # Closes below previous low
                mss_signals.append({
                    'type': 'bearish',
                    'price': df['close'].iloc[i],
                    'time': df.index[i]
                })
        
        return mss_signals
    
    def analyze(self, data: pd.DataFrame) -> dict:
        """
        Analyze market data using multiple ICT concepts and generate trading signals.
        """
        # Get current time and check trade frequency
        current_time = data.index[-1]
        if self.last_trade_time:
            if (current_time.date() != self.last_trade_time.date()):
                self.trades_today = 0
            if self.trades_today >= self.max_daily_trades:
                return None
                
        # Get market conditions
        daily_bias = self.get_daily_bias(data)
        trend = self.identify_strong_trend(data)
        volatility = self.calculate_volatility(data)
        atr = self.calculate_atr(data)
        
        # Skip trading if volatility is too high
        if volatility > 0.30:  # Higher volatility threshold for gold
            return None
            
        # Get current price and recent price action
        current_price = data['close'].iloc[-1]
        recent_high = data['high'].iloc[-5:].max()  # Increased lookback for gold
        recent_low = data['low'].iloc[-5:].min()
        
        # Identify patterns
        liquidity_levels = self.identify_liquidity_levels(data)
        mss_signals = self.identify_market_structure_shift(data)
        
        # Calculate potential signals with improved risk management
        signals = []
        
        # 1. Strong Trend Following (highest priority)
        if trend == 'strong_bullish' and daily_bias == 'bullish':
            stop_loss_dollars = 2.0 * atr  # $20-30 typical range for gold
            stop_loss = current_price - stop_loss_dollars
            take_profit = current_price + (stop_loss_dollars * 2)  # 2:1 risk-reward ratio
            signals.append({
                'action': 'buy',
                'price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'stop_loss_dollars': stop_loss_dollars,
                'reason': 'Strong Bullish Trend',
                'score': 90,
                'time': current_time
            })
            
        elif trend == 'strong_bearish' and daily_bias == 'bearish':
            stop_loss_dollars = 2.0 * atr
            stop_loss = current_price + stop_loss_dollars
            take_profit = current_price - (stop_loss_dollars * 2)
            signals.append({
                'action': 'sell',
                'price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'stop_loss_dollars': stop_loss_dollars,
                'reason': 'Strong Bearish Trend',
                'score': 90,
                'time': current_time
            })
            
        # 2. Liquidity Pool Strategy (with trend confirmation)
        if current_price < recent_low and trend in ['strong_bullish', 'bullish', 'neutral']:
            stop_loss_dollars = 1.5 * atr  # $15-25 typical range for gold
            stop_loss = current_price - stop_loss_dollars
            take_profit = current_price + (stop_loss_dollars * 2)
            signals.append({
                'action': 'buy',
                'price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'stop_loss_dollars': stop_loss_dollars,
                'reason': 'Liquidity Pool - Buy at discount',
                'score': 85,
                'time': current_time
            })
            
        if current_price > recent_high and trend in ['strong_bearish', 'bearish', 'neutral']:
            stop_loss_dollars = 1.5 * atr
            stop_loss = current_price + stop_loss_dollars
            take_profit = current_price - (stop_loss_dollars * 2)
            signals.append({
                'action': 'sell',
                'price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'stop_loss_dollars': stop_loss_dollars,
                'reason': 'Liquidity Pool - Sell at premium',
                'score': 85,
                'time': current_time
            })
            
        # 3. Market Structure Shift (with trend confirmation)
        for mss in mss_signals:
            if mss['time'] == current_time:
                if mss['type'] == 'bullish' and trend in ['strong_bullish', 'bullish', 'neutral']:
                    stop_loss_dollars = 1.5 * atr
                    stop_loss = current_price - stop_loss_dollars
                    take_profit = current_price + (stop_loss_dollars * 2)
                    signals.append({
                        'action': 'buy',
                        'price': current_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'stop_loss_dollars': stop_loss_dollars,
                        'reason': 'Market Structure Shift - Bullish',
                        'score': 85,
                        'time': current_time
                    })
                elif mss['type'] == 'bearish' and trend in ['strong_bearish', 'bearish', 'neutral']:
                    stop_loss_dollars = 1.5 * atr
                    stop_loss = current_price + stop_loss_dollars
                    take_profit = current_price - (stop_loss_dollars * 2)
                    signals.append({
                        'action': 'sell',
                        'price': current_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'stop_loss_dollars': stop_loss_dollars,
                        'reason': 'Market Structure Shift - Bearish',
                        'score': 85,
                        'time': current_time
                    })
        
        # Select best signal
        if signals:
            best_signal = max(signals, key=lambda x: x['score'])
            if best_signal['score'] >= self.min_score_threshold:
                # Verify risk-reward ratio
                risk = best_signal['stop_loss_dollars']
                reward = abs(best_signal['take_profit'] - best_signal['price'])
                if reward / risk >= self.min_risk_reward:
                    self.trades_today += 1
                    self.last_trade_time = current_time
                    return best_signal
        
        return None
        
    def calculate_position_size(self, account_balance: float, stop_loss_pips: float) -> float:
        """
        Calculate position size based on risk management rules
        """
        risk_amount = account_balance * (self.risk_percentage / 100)
        # Gold moves in dollars, not pips
        position_size = risk_amount / stop_loss_pips
        return round(position_size, 2)  # Round to 2 decimal places

    def update(self, price_info):
        """Update strategy with new price information"""
        self.current_price = price_info
        
        # Add price to historical data
        self.price_data.append({
            'timestamp': datetime.now(),
            'bid': price_info['bid'],
            'ask': price_info['ask']
        })
        
        # Keep only last 100 price points
        if len(self.price_data) > 100:
            self.price_data = self.price_data[-100:]
            
        return self.generate_signals()
        
    def generate_signals(self):
        """Generate trading signals based on ICT concepts"""
        signals = []
        
        if len(self.price_data) < 20:  # Need minimum data points
            return signals
            
        # Convert price data to DataFrame
        df = pd.DataFrame(self.price_data)
        
        # Calculate basic indicators
        df['mid'] = (df['bid'] + df['ask']) / 2
        df['sma20'] = df['mid'].rolling(window=20).mean()
        df['high'] = df['mid'].rolling(window=5).max()
        df['low'] = df['mid'].rolling(window=5).min()
        
        # Get latest data point
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Simple ICT-based rules
        # 1. Price above/below SMA20
        # 2. Price at significant high/low
        
        if latest['mid'] > latest['sma20'] and prev['mid'] <= prev['sma20']:
            signals.append({
                'symbol': self.symbol,
                'action': 'BUY',
                'price': self.current_price['ask'],
                'volume': self.calculate_position_size(self.risk_percentage, 100),
                'stop_loss': latest['low'],
                'take_profit': latest['high'] + (latest['high'] - latest['low'])
            })
            
        elif latest['mid'] < latest['sma20'] and prev['mid'] >= prev['sma20']:
            signals.append({
                'symbol': self.symbol,
                'action': 'SELL',
                'price': self.current_price['bid'],
                'volume': self.calculate_position_size(self.risk_percentage, 100),
                'stop_loss': latest['high'],
                'take_profit': latest['low'] - (latest['high'] - latest['low'])
            })
            
        return signals 