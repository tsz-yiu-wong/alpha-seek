# handler.py
import asyncio
import time
import json # Assuming normalized_data might need json processing if coming raw
import traceback # For detailed error logging
from ..event_bus_backup import EventBus # Import from parent backend directory
from .fetchers.dex_api import DexScreenerAPI
from .normalizer import normalize_data_for_database
from .database import write_token_data

# 初始化事件总线
event_bus = EventBus() 


async def main_data_loop(time_interval=30):
    """主数据处理循环：获取、标准化、写入数据库、发布单个代币数据"""
    while True:
        start_time = time.time()
        try:
            async with DexScreenerAPI() as data_fetcher:
                # 1. Fetch data
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Fetching data...")
                # Assuming these fetch calls return data structured appropriately
                token_list = await data_fetcher.only_solana_token_profiles_list()
                raw_token_data = await data_fetcher.fetch_data_for_token_profiles_list(token_list, "solana")

                # 2. Normalize data
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Normalizing data...")
                # Let's assume normalized_data is a list of dicts, each dict representing a token
                # and having a key like 'pairAddress' or 'symbol' to identify the token.
                # Example structure: [{'pairAddress': 'addr1', 'priceUsd': '100', ...}, {'pairAddress': 'addr2', ...}]
                normalized_data_list = await normalize_data_for_database(raw_token_data) # Assuming it returns a list

                # 3. Write batch data to database (optional, consider if still needed)
                # Keeping batch write for now as per original logic.
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Writing batch data to database...")
                # await write_token_data(normalized_data_list) # Pass the list

                # 4. Publish individual token data to event bus
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Publishing individual token data to event bus...")
                if isinstance(normalized_data_list, list): # Check if it's iterable list
                    published_count = 0
                    for token_data in normalized_data_list:
                        # Need a unique identifier for the channel. Assume 'pairAddress' is unique.
                        # TODO: Confirm the actual unique identifier key in token_data (e.g., 'pairAddress', 'symbol', 'baseToken.symbol').
                        token_identifier = token_data.get('pairAddress')
                        if token_identifier:
                            channel = f"token_data:{token_identifier}"
                            # Publish the single token data dictionary
                            event_bus.publish(channel, token_data)
                            published_count += 1
                        else:
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Warning: Missing identifier ('pairAddress') for token data: {token_data}")
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Published data for {published_count} tokens.")
                elif normalized_data_list: # Handle cases where it might not be a list but still has data
                     print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Warning: normalized_data is not a list, cannot publish individually. Data: {normalized_data_list}")


                elapsed_time = time.time() - start_time
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Cycle complete in {elapsed_time:.2f} seconds.")

        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error in main_data_loop: {e}")
            # Log traceback for detailed debugging
            traceback.print_exc()

        # 计算需要等待的时间
        wait_time = max(0, time_interval - (time.time() - start_time))
        if wait_time > 0:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Waiting for {wait_time:.2f} seconds...")
            await asyncio.sleep(wait_time)
        else:
             print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Loop took longer than interval ({time.time() - start_time:.2f}s), running next cycle immediately.")


# 如果此脚本作为主程序运行
if __name__ == "__main__":
    try:
        print("Starting main data loop...")
        asyncio.run(main_data_loop(time_interval=30))
    except KeyboardInterrupt:
        print("Data loop stopped by user.")
