import aiohttp
import asyncio
import json
from typing import Dict, Any, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class CoinMarketCapAPI:

    # Initialize
    def __init__(self):
        self.session = None

    async def __aenter__(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            self.session = None

    async def close_session(self):
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    # Call API
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:

        if self.session is None:
            self.session = aiohttp.ClientSession()

        url = f"https://pro-api.coinmarketcap.com/v1/{endpoint}"
        headers = {
            "Accepts": "application/json", 
            "X-CMC_PRO_API_KEY": os.getenv('CMC_API_KEY')
        }
        
        # Check if API key exists
        if not headers["X-CMC_PRO_API_KEY"]:
            print("🚨 Error: CMC_API_KEY not found in environment variables.")
            return {}

        try:
            async with self.session.get(url, headers=headers, params=params) as response:
                response_text = await response.text()
                if response.status == 200:
                    try:
                        data = await response.json(content_type=None) # Try decoding JSON regardless of content-type
                        # Optionally save to data.json (consider if this is needed long-term)
                        # try:
                        #     with open('data.json', 'w', encoding='utf-8') as f:
                        #         json.dump(data, f, ensure_ascii=False, indent=4)
                        # except IOError as e:
                        #      print(f"Error writing to data.json: {e}")
                        return data
                    except json.JSONDecodeError:
                         print(f"🚨 Error: Could not decode JSON response from {url}. Status: {response.status}. Response text: {response_text}")
                         return {}
                else:
                    print(f"⚠️ Error: API returned status {response.status} - {response_text}")
                    return {}
        except aiohttp.ClientError as e: # Catch specific client errors
            print(f"🚨 Network/Client Error making request to {url}: {e}")
            return {}
        except Exception as e:
            print(f"🚨 Unexpected Error making request to {url}: {e}")
            return {}


    async def get_latest_listings(self, limit: int = 10, convert: str = "USD") -> List[Dict[str, Any]]:
        """获取最新的加密货币列表"""
        params = {"limit": limit, "convert": convert}
        data = await self._make_request("cryptocurrency/listings/latest", params)
        return data.get("data", []) # Return empty list if 'data' key is missing or request failed

    async def get_crypto_price(self, symbol: str, convert: str = "USD") -> Optional[float]:
        """获取指定加密货币的价格
        Args:
            - symbol (str): 加密货币符号，如 "BTC"
            - convert (str): 转换货币，默认为 "USD"

        Returns:
            - Optional[float]: 价格（指定货币）或 None
        """
        params = {"symbol": symbol, "convert": convert}
        data = await self._make_request("cryptocurrency/quotes/latest", params)

        # Navigate through the nested structure safely
        crypto_data = data.get("data", {}).get(symbol.upper()) # CMC API often uses uppercase symbols
        if crypto_data and "quote" in crypto_data and convert in crypto_data["quote"]:
            return crypto_data["quote"][convert].get("price")
        else:
            print(f"Could not find price data for symbol '{symbol}' in convert '{convert}'. Response: {data}")
            return None

    # Note: fetch_mcm_data seems redundant as get_latest_listings covers the same endpoint.
    # If specific logic was intended for _make_request_to_mcm, it should be clarified.
    # async def fetch_mcm_data(self) -> List[Dict[str, Any]]:
    #     data = await self._make_request("cryptocurrency/listings/latest") # Uses the standard _make_request now
    #     return data.get("data", [])
