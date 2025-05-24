# backend/runner.py
# 主控文件：加载策略 + 订阅数据 + 分发消息 + 触发交易

import asyncio
import json
import time # Import time module
import traceback # For detailed error logging
# Assuming strategies are in a 'strategies' sibling directory
# Make sure StrategyA and StrategyB have an `on_data` method
from backend.strategies import StrategyA, StrategyB # Corrected import path
# Import BaseStrategy and Signal for type hinting and checks if needed
from backend.strategies.base import BaseStrategy, Signal
# Assuming event_bus is defined in data.handler or data.event_bus
# Correct path assuming event_bus.py is in backend/data/
# Assuming you might have refactored event bus location
# from backend.event_bus import EventBus # Import from backend directory
# Using the provided backup event bus for now
from backend.event_bus_backup import EventBus
# Import the trade executor
# Correct path assuming trader.py is in backend/trade/
from backend.trade.trader import TradeExecutor, MockTradingModule, SolanaTradingModule # Import SolanaTradingModule

# --- Configuration --- #

# Choose the trading module: SolanaTradingModule for live trading, MockTradingModule for testing
USE_LIVE_TRADING = False # Set to True for actual trading
DEFAULT_WALLET_INDEX = 0 # Define which wallet to use from config
RPC_URL = "https://api.mainnet-beta.solana.com" # Or use a custom/private RPC

if USE_LIVE_TRADING:
    actual_trading_module = SolanaTradingModule(rpc_url=RPC_URL)
else:
    actual_trading_module = MockTradingModule()
    print("\n*** RUNNING WITH MOCK TRADING MODULE. NO REAL TRADES WILL BE EXECUTED. ***\n")

# --- Initialization --- #

# Initialize Event Bus
event_bus = EventBus() # Assuming singleton or shared instance logic

# Initialize Trade Executor with the chosen trading module and wallet
trade_executor = TradeExecutor(actual_trading_module, default_wallet_index=DEFAULT_WALLET_INDEX)

# Load Strategies
# Keys MUST match the identifier used by handler.py in the channel name (e.g., pairAddress)
# Strategy __init__ takes (token_symbol, pair_address)
strategies: dict[str, BaseStrategy] = {
    # Example WIF/SOL pair on Raydium (check DexScreener for the correct pair address)
    "6_8_4_3_1_2": StrategyA(token_symbol="WIF", pair_address="6_8_4_3_1_2"), # Placeholder pair address
    # Example BONK/SOL pair
    "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263": StrategyA(token_symbol="BONK", pair_address="DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"),
    # Add more strategies here, ensuring the key matches the pairAddress from DexScreener
    # that handler.py uses for the channel.
}
# Update runner strategies dict keys based on the actual pair addresses used in handler.py
# Find correct pair addresses on DexScreener for the tokens you want to trade.
# For example, SOL/USDC is EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
# If StrategyA is for SOL/USDC, the entry should be:
# "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": StrategyA(token_symbol="USDC", pair_address="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"),

# Let's update the examples to use the ones from the original file if they are still relevant
strategies = {
    # SOL/USDC pair address
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": StrategyA(token_symbol="USDC", pair_address="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"),
    # BONK/SOL pair address
    "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263": StrategyA(token_symbol="BONK", pair_address="DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"),
    # If you have StrategyB, add it here:
    # "AnotherPairAddress": StrategyB(token_symbol="OTHER", pair_address="AnotherPairAddress"),
}


# --- Event Bus Subscription --- #

def handle_token_data_sync(channel, data):
    """Synchronous wrapper to schedule the async handler."""
    # Use asyncio.create_task to run the async handler without blocking the event bus publish loop
    asyncio.create_task(handle_token_data_async(channel, data))

async def handle_token_data_async(channel, data):
    """Async callback function to handle incoming token data from the event bus."""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S') # Get current time for logging
    # print(f"[{timestamp}] Received data on channel {channel}") # Can be verbose
    # Extract token identifier from channel name (assuming format "token_data:identifier")
    try:
        # The identifier published by handler.py is the pairAddress
        pair_address = channel.split(":", 1)[1]
    except IndexError:
        print(f"[{timestamp}] Error: Could not extract pair address from channel: {channel}")
        return

    # Find the corresponding strategy using the pair_address as the key
    strategy = strategies.get(pair_address)
    if strategy:
        # print(f"[{timestamp}] Dispatching data to strategy for pair: {pair_address}")
        try:
            # Strategy's on_data method is async
            signal: Signal | None = await strategy.on_data(data)

            if signal:
                # Ensure the signal is the correct type (optional but good practice)
                if isinstance(signal, Signal) and all(hasattr(signal, attr) for attr in signal._fields):
                    print(f"[{timestamp}] Strategy for {strategy.token_symbol} ({pair_address}) generated signal: {signal}")
                    # Trigger trade execution (handle_signal is now async)
                    await trade_executor.handle_signal(signal)
                else:
                     print(f"[{timestamp}] Strategy for {pair_address} returned invalid signal type: {signal}")
            # else:
            #     print(f"[{timestamp}] Strategy for {pair_address} did not generate signal.") # Can be verbose

        except Exception as e:
            print(f"[{timestamp}] Error processing data or signal for strategy {pair_address}: {e}")
            traceback.print_exc()
    # else:
        # This is expected if handler publishes data for pairs without active strategies
        # print(f"[{timestamp}] No strategy found for pair address: {pair_address}")
        pass # Keep this commented out unless debugging

# Subscribe the handler to all relevant channels
def subscribe_to_channels():
    """Subscribes the data handler to event bus channels for configured strategies."""
    print("Subscribing runner to token data channels...")
    subscribed_count = 0
    if not strategies:
         print("Warning: No strategies defined in runner.py")
         return

    for pair_address in strategies.keys():
        channel = f"token_data:{pair_address}"
        # Subscribe the SYNCHRONOUS wrapper, which then schedules the async task
        event_bus.subscribe(channel, handle_token_data_sync)
        print(f"Subscribed handler to channel: {channel}")
        subscribed_count += 1
    print(f"Runner subscribed to {subscribed_count} channels.")

# --- Main Execution Logic --- #

async def main():
    """Main execution loop for the runner."""
    print("Runner starting...")
    subscribe_to_channels()
    print(f"Runner subscribed. Using {'Live Trading (Solana)' if USE_LIVE_TRADING else 'Mock Trading'}.")
    print("Waiting for data events from EventBus...")

    # Keep the runner alive to listen for events.
    await asyncio.Future() # Keep running indefinitely


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nRunner stopped by user.")
    except Exception as e:
        print(f"\nRunner crashed: {e}")
        traceback.print_exc()
