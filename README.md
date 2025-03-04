# Forex Trading Bot

A flexible and modular forex trading bot that can implement various trading strategies using MetaTrader5.

## Features

- Modular strategy implementation system
- Risk management controls
- Real-time market data processing
- Configurable trading parameters
- Multiple timeframe support

## Setup

1. Install MetaTrader5 on your system
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your MT5 credentials in `.env` file:
   ```
   MT5_LOGIN=your_login
   MT5_PASSWORD=your_password
   MT5_SERVER=your_server
   ```

## Project Structure

- `trading_bot.py`: Main bot implementation
- `strategies/`: Directory containing trading strategies
- `utils/`: Utility functions for data processing and analysis
- `config.py`: Configuration management
- `risk_manager.py`: Risk management system

## Usage

1. Create your strategy by implementing the base Strategy class
2. Configure your trading parameters in config.py
3. Run the bot:
   ```bash
   python trading_bot.py
   ```

## Disclaimer

This trading bot is for educational purposes only. Always test thoroughly in a demo account before using real money. 