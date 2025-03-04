from trading_bot import ForexTradingBot
from strategies.ict_combined_strategy import ICTCombinedStrategy
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ict_bot.log'),
        logging.StreamHandler()
    ]
)

def main():
    # Initialize the ICT Combined Strategy
    strategy = ICTCombinedStrategy(
        symbol='EURUSD',
        timeframe='15m',
        risk_percentage=1.0
    )
    
    # Initialize the trading bot
    bot = ForexTradingBot(
        strategy=strategy,
        api_key='YOUR_API_KEY',
        api_secret='YOUR_API_SECRET',
        test_mode=True  # Set to False for live trading
    )
    
    logging.info("Starting ICT Trading Bot...")
    logging.info(f"Trading {strategy.symbol} on {strategy.timeframe} timeframe")
    logging.info(f"Risk per trade: {strategy.risk_percentage}%")
    
    try:
        # Start the bot
        bot.run()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Error running bot: {str(e)}")
    finally:
        bot.close()

if __name__ == "__main__":
    main() 