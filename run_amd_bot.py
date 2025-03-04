from trading_bot import ForexTradingBot
from strategies.amd_strategy import AMDStrategy

def main():
    # Initialize the AMD Strategy
    # Trading EURUSD on 15-minute timeframe
    strategy = AMDStrategy(
        symbol="EURUSD",
        timeframe=15,  # 15 minutes
        risk_percentage=1.0  # 1% risk per trade
    )
    
    # Create and run the trading bot
    bot = ForexTradingBot(strategy)
    print("Starting AMD Trading Bot...")
    bot.run()

if __name__ == "__main__":
    main() 