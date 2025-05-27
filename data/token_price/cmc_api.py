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


    async def get_latest_listings(self, convert: str = "USD") -> List[Dict[str, Any]]:
        """获取最新的加密货币列表"""
        params = {"convert": convert}
        data = await self._make_request("cryptocurrency/listings/latest", params)
        return data.get("data", []) # Return empty list if 'data' key is missing or request failed

    async def get_categories(self) -> List[Dict[str, Any]]:
        """获取加密货币类别列表"""
        data = await self._make_request("cryptocurrency/categories")
        return data.get("data", [])
    
    async def get_category_listings(self, category_name: str) -> List[Dict[str, Any]]:
        categories_path = os.path.join(os.path.dirname(__file__), "cmc_categories.json")
        with open(categories_path, 'r') as f:
            categories = json.load(f)
        category_id = next((cat['id'] for cat in categories if cat['name'] == category_name), None)
        if not category_id:
            print(f"Category '{category_name}' not found")
            return []
        
        params = {"id": category_id, "limit": 30}
        data = await self._make_request(f"cryptocurrency/category", params)
        return data.get("data", [])

if __name__ == "__main__":
    async def main():
        async with CoinMarketCapAPI() as api:
            latest_listings = await api.get_latest_listings()
            print(len(latest_listings))
            with open('cmc_latest_listings.json', 'w') as f:
                json.dump(latest_listings, f, indent=4)
            category_listings = await api.get_category_listings("Binance Alpha")
            print(len(category_listings))
            with open('cmc_Binance_Alpha_data.json', 'w') as f:
                json.dump(category_listings, f, indent=4)
    asyncio.run(main())