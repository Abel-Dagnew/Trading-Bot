import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from strategies.ict_combined_strategy import ICTCombinedStrategy
from backtesting.backtest import Backtest

def download_data(symbol, timeframe, start_date, end_date):
    """Download historical data from Yahoo Finance"""
    ticker = yf.Ticker(symbol)
    
    # Download data in 7-day chunks to avoid limitations
    all_data = pd.DataFrame()
    current_start = start_date
    
    while current_start < end_date:
        current_end = min(current_start + timedelta(days=7), end_date)
        print(f"Downloading chunk from {current_start} to {current_end}")
        
        chunk = ticker.history(start=current_start, end=current_end, interval=timeframe)
        if not chunk.empty:
            all_data = pd.concat([all_data, chunk])
        
        current_start = current_end
    
    if all_data.empty:
        return pd.DataFrame()
    
    # Remove any duplicate data points
    all_data = all_data[~all_data.index.duplicated(keep='first')]
    
    # Rename columns to match our strategy's expectations
    all_data = all_data.rename(columns={
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    })
    
    return all_data

def main():
    # Initialize strategy
    strategy = ICTCombinedStrategy(
        symbol='GC=F',  # Yahoo Finance symbol for Gold Futures
        timeframe='1m',
        risk_percentage=1.0
    )
    
    # Download historical data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=14)  # Test on last 14 days
    
    print(f"Downloading data from {start_date} to {end_date}")
    data = download_data('GC=F', '1m', start_date, end_date)
    
    if data.empty:
        print("No data downloaded. Please check your internet connection and try again.")
        return
    
    print(f"Downloaded {len(data)} data points")
    
    # Initialize backtest
    backtest = Backtest(strategy, initial_balance=10000)
    
    # Run backtest
    print("\nRunning backtest...")
    results = backtest.run(data)
    
    # Plot results
    backtest.plot_results(data)
    
    # Print detailed results
    print("\nDetailed Trade History:")
    for trade in results['trades']:
        print(f"\nEntry Time: {trade['entry_time']}")
        print(f"Entry Price: ${trade['entry_price']:.2f}")
        print(f"Exit Time: {trade['exit_time']}")
        print(f"Exit Price: ${trade['exit_price']:.2f}")
        print(f"Profit: ${trade['profit']:.2f}")
        print(f"Exit Type: {trade['type']}")
        
    # Print daily performance
    print("\nDaily Performance Analysis:")
    daily_profits = {}
    for trade in results['trades']:
        date = trade['entry_time'].date()
        if date not in daily_profits:
            daily_profits[date] = 0
        daily_profits[date] += trade['profit']
    
    for date, profit in sorted(daily_profits.items()):
        print(f"{date}: ${profit:.2f}")
        
    # Print risk metrics
    print("\nRisk Analysis:")
    print(f"Average Win: ${sum(t['profit'] for t in results['trades'] if t['profit'] > 0) / len([t for t in results['trades'] if t['profit'] > 0]):.2f}")
    print(f"Average Loss: ${sum(t['profit'] for t in results['trades'] if t['profit'] <= 0) / len([t for t in results['trades'] if t['profit'] <= 0]):.2f}")
    print(f"Largest Win: ${max((t['profit'] for t in results['trades']), default=0):.2f}")
    print(f"Largest Loss: ${min((t['profit'] for t in results['trades']), default=0):.2f}")
    print(f"Average Trade Duration: {sum((t['exit_time'] - t['entry_time']).total_seconds() / 3600 for t in results['trades']) / len(results['trades']):.2f} hours")

if __name__ == "__main__":
    main() 