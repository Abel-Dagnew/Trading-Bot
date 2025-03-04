from trading_bot import ForexTradingBot
from strategies.ma_crossover_strategy import MACrossoverStrategy

def main():
    # Create strategy instance
    strategy = MACrossoverStrategy(
        symbol="EURUSD",  # Trading pair
        timeframe=15,     # 15-minute timeframe
        fast_period=10,   # Fast MA period
        slow_period=20,   # Slow MA period
        risk_percentage=1.0  # Risk 1% per trade
    )
    
    # Create and run trading bot
    bot = ForexTradingBot(strategy)
    bot.run()

if __name__ == "__main__":
    main() 