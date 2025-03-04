from typing import List, Dict
import pandas as pd
from .base_strategy import BaseStrategy

class StrategyManager:
    def __init__(self, strategies: List[BaseStrategy]):
        self.strategies = strategies
        self.active_strategy = None
        self.last_trade_time = None
        self.min_trade_interval = pd.Timedelta(hours=4)  # Minimum time between trades
        
    def analyze_all(self, data: pd.DataFrame) -> Dict:
        """
        Analyze market data using all strategies and select the best opportunity.
        
        Args:
            data (pd.DataFrame): Historical price data
            
        Returns:
            Dict: Best trading opportunity or None if no valid signals
        """
        best_signal = None
        best_score = 0
        
        # Check if enough time has passed since last trade
        if self.last_trade_time is not None:
            time_since_last_trade = pd.Timestamp.now() - self.last_trade_time
            if time_since_last_trade < self.min_trade_interval:
                return None
        
        # Analyze each strategy
        for strategy in self.strategies:
            signal = strategy.analyze(data)
            if signal is not None:
                # Calculate strategy score based on multiple factors
                score = self._calculate_strategy_score(signal, data)
                
                if score > best_score:
                    best_score = score
                    best_signal = signal
                    self.active_strategy = strategy
        
        if best_signal is not None:
            self.last_trade_time = pd.Timestamp.now()
            return best_signal
        
        return None
    
    def _calculate_strategy_score(self, signal: Dict, data: pd.DataFrame) -> float:
        """
        Calculate a score for the trading signal based on multiple factors.
        
        Args:
            signal (Dict): Trading signal from strategy
            data (pd.DataFrame): Historical price data
            
        Returns:
            float: Strategy score (0-100)
        """
        score = 0
        
        # Factor 1: Daily Bias Alignment (30 points)
        daily_bias = self.active_strategy.get_daily_bias(data)
        if (signal['action'] == 'buy' and daily_bias == 'bullish') or \
           (signal['action'] == 'sell' and daily_bias == 'bearish'):
            score += 30
        
        # Factor 2: Risk-Reward Ratio (20 points)
        risk = abs(signal['price'] - signal['stop_loss'])
        reward = abs(signal['take_profit'] - signal['price'])
        rr_ratio = reward / risk
        if rr_ratio >= 2:
            score += 20
        elif rr_ratio >= 1.5:
            score += 15
        
        # Factor 3: Liquidity Level Proximity (20 points)
        liquidity_levels = self.active_strategy.identify_liquidity_levels(data)
        current_price = data['close'].iloc[-1]
        
        if signal['action'] == 'buy':
            nearest_low = min(liquidity_levels['recent_lows'], key=lambda x: abs(x - current_price))
            if abs(current_price - nearest_low) < risk:
                score += 20
        else:
            nearest_high = min(liquidity_levels['recent_highs'], key=lambda x: abs(x - current_price))
            if abs(current_price - nearest_high) < risk:
                score += 20
        
        # Factor 4: Market Structure (30 points)
        # Check if price is near a Fair Value Gap or Order Block
        fvgs = self.active_strategy.identify_fair_value_gaps(data)
        order_blocks = self.active_strategy.identify_order_blocks(data)
        
        for fvg in fvgs:
            if fvg['type'] == signal['action']:
                if fvg['low'] <= current_price <= fvg['high']:
                    score += 15
                    break
        
        for ob in order_blocks:
            if ob['type'] == signal['action']:
                if ob['low'] <= current_price <= ob['high']:
                    score += 15
                    break
        
        return score
    
    def get_active_strategy(self) -> BaseStrategy:
        """Get the currently active strategy"""
        return self.active_strategy
    
    def reset(self):
        """Reset the strategy manager state"""
        self.active_strategy = None
        self.last_trade_time = None 