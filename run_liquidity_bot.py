from trading_bot import ForexTradingBot
from strategies.liquidity_strategy import LiquidityStrategy

def main():
    # Initialize the Liquidity Strategy
    # Trading EURUSD on 15-minute timeframe
    strategy = LiquidityStrategy(
        symbol="EURUSD",
        timeframe=15,  # 15 minutes
        risk_percentage=1.0  # 1% risk per trade
    )
    
    # Create and run the trading bot
    bot = ForexTradingBot(strategy)
    print("Starting Liquidity Trading Bot...")
    bot.run()

if __name__ == "__main__":
    main() 