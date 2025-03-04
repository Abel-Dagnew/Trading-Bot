import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import matplotlib.pyplot as plt
from strategies.ict_combined_strategy import ICTCombinedStrategy

class Backtest:
    def __init__(self, strategy: ICTCombinedStrategy, initial_balance: float = 10000):
        self.strategy = strategy
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions = []
        self.trades = []
        self.equity_curve = []
        
    def run(self, data: pd.DataFrame) -> Dict:
        """
        Run backtest on historical data
        
        Args:
            data (pd.DataFrame): Historical price data
            
        Returns:
            Dict: Backtest results
        """
        self.balance = self.initial_balance
        self.positions = []
        self.trades = []
        self.equity_curve = []
        
        for i in range(len(data)):
            current_data = data.iloc[:i+1]
            current_price = current_data['close'].iloc[-1]
            
            # Update existing positions
            self._update_positions(current_price)
            
            # Generate new signals
            signal = self.strategy.analyze(current_data)
            
            if signal and not self.positions:  # Only enter if no current position
                self._enter_position(signal, current_price)
            
            # Record equity
            self.equity_curve.append(self._calculate_equity(current_price))
        
        return self._generate_results()
    
    def _update_positions(self, current_price: float):
        """Update existing positions"""
        for position in self.positions[:]:  # Create a copy to iterate
            position['current_time'] = current_price  # Update current time
            
            if position['action'] == 'buy':
                if current_price >= position['take_profit']:
                    # Close at take profit
                    profit = (position['take_profit'] - position['entry_price']) * position['size']
                    self.balance += profit
                    self.trades.append({
                        'entry_time': position['entry_time'],
                        'exit_time': position['current_time'],
                        'entry_price': position['entry_price'],
                        'exit_price': position['take_profit'],
                        'profit': profit,
                        'type': 'tp'
                    })
                    self.positions.remove(position)
                elif current_price <= position['stop_loss']:
                    # Close at stop loss
                    loss = (position['stop_loss'] - position['entry_price']) * position['size']
                    self.balance += loss
                    self.trades.append({
                        'entry_time': position['entry_time'],
                        'exit_time': position['current_time'],
                        'entry_price': position['entry_price'],
                        'exit_price': position['stop_loss'],
                        'profit': loss,
                        'type': 'sl'
                    })
                    self.positions.remove(position)
            else:  # sell position
                if current_price <= position['take_profit']:
                    # Close at take profit
                    profit = (position['entry_price'] - position['take_profit']) * position['size']
                    self.balance += profit
                    self.trades.append({
                        'entry_time': position['entry_time'],
                        'exit_time': position['current_time'],
                        'entry_price': position['entry_price'],
                        'exit_price': position['take_profit'],
                        'profit': profit,
                        'type': 'tp'
                    })
                    self.positions.remove(position)
                elif current_price >= position['stop_loss']:
                    # Close at stop loss
                    loss = (position['entry_price'] - position['stop_loss']) * position['size']
                    self.balance += loss
                    self.trades.append({
                        'entry_time': position['entry_time'],
                        'exit_time': position['current_time'],
                        'entry_price': position['entry_price'],
                        'exit_price': position['stop_loss'],
                        'profit': loss,
                        'type': 'sl'
                    })
                    self.positions.remove(position)
    
    def _enter_position(self, signal: Dict, current_price: float):
        """Enter a new position"""
        # Use stop_loss_dollars directly for position sizing
        position_size = self.strategy.calculate_position_size(
            self.balance,
            signal['stop_loss_dollars']  # Use dollar-based stop loss
        )
        
        self.positions.append({
            'entry_time': signal['time'],
            'current_time': signal['time'],
            'entry_price': current_price,
            'stop_loss': signal['stop_loss'],
            'take_profit': signal['take_profit'],
            'size': position_size,
            'action': signal['action']
        })
    
    def _calculate_equity(self, current_price: float) -> float:
        """Calculate current equity including open positions"""
        equity = self.balance
        for position in self.positions:
            if position['action'] == 'buy':
                profit = (current_price - position['entry_price']) * position['size']
            else:
                profit = (position['entry_price'] - current_price) * position['size']
            equity += profit
        return equity
    
    def _generate_results(self) -> Dict:
        """Generate backtest results"""
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
                'final_balance': self.initial_balance,
                'total_return': 0,
                'sharpe_ratio': 0,
                'trades': [],  # Add empty trades list
                'equity_curve': self.equity_curve
            }
        
        # Calculate basic statistics
        winning_trades = [t for t in self.trades if t['profit'] > 0]
        losing_trades = [t for t in self.trades if t['profit'] <= 0]
        
        total_profit = sum(t['profit'] for t in winning_trades)
        total_loss = abs(sum(t['profit'] for t in losing_trades))
        
        # Calculate drawdown
        peak = self.initial_balance
        max_drawdown = 0
        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        # Calculate Sharpe Ratio (assuming risk-free rate of 2%)
        returns = pd.Series(self.equity_curve).pct_change().dropna()
        sharpe_ratio = np.sqrt(252) * (returns.mean() - 0.02) / returns.std() if len(returns) > 0 else 0
        
        return {
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(self.trades) * 100,
            'profit_factor': total_profit / total_loss if total_loss > 0 else float('inf'),
            'max_drawdown': max_drawdown * 100,
            'final_balance': self.equity_curve[-1],
            'total_return': (self.equity_curve[-1] - self.initial_balance) / self.initial_balance * 100,
            'sharpe_ratio': sharpe_ratio,
            'trades': self.trades,
            'equity_curve': self.equity_curve
        }
    
    def plot_results(self, data: pd.DataFrame):
        """Plot backtest results"""
        results = self._generate_results()
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        
        # Plot price and trades
        ax1.plot(data.index, data['close'], label='Price', color='blue')
        
        # Plot entry points
        for trade in results['trades']:
            if trade['profit'] > 0:
                ax1.scatter(trade['entry_time'], trade['entry_price'], 
                          color='green', marker='^', s=100)
                ax1.scatter(trade['exit_time'], trade['exit_price'], 
                          color='green', marker='v', s=100)
            else:
                ax1.scatter(trade['entry_time'], trade['entry_price'], 
                          color='red', marker='^', s=100)
                ax1.scatter(trade['exit_time'], trade['exit_price'], 
                          color='red', marker='v', s=100)
        
        ax1.set_title('Price Chart with Trades')
        ax1.legend()
        
        # Plot equity curve
        ax2.plot(data.index, results['equity_curve'], label='Equity', color='green')
        ax2.set_title('Equity Curve')
        ax2.legend()
        
        plt.tight_layout()
        plt.show()
        
        # Print results
        print("\nBacktest Results:")
        print(f"Total Trades: {results['total_trades']}")
        print(f"Winning Trades: {results['winning_trades']}")
        print(f"Losing Trades: {results['losing_trades']}")
        print(f"Win Rate: {results['win_rate']:.2f}%")
        print(f"Profit Factor: {results['profit_factor']:.2f}")
        print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
        print(f"Final Balance: ${results['final_balance']:.2f}")
        print(f"Total Return: {results['total_return']:.2f}%")
        print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}") 