from trading_bot import ForexTradingBot
from strategies.ma_crossover_strategy import MACrossoverStrategy

def main():
    # Initialize the MA Crossover strategy
    # Trading EURUSD on 15-minute timeframe
    strategy = MACrossoverStrategy(
        symbol="EURUSD",
        timeframe=15,  # 15 minutes
        fast_period=10,
        slow_period=20,
        risk_percentage=1.0  # 1% risk per trade
    )
    
    # Create and run the trading bot
    bot = ForexTradingBot(strategy)
    print("Starting trading bot...")
    bot.run()

if __name__ == "__main__":
    main() 