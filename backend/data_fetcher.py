import aiohttp
import asyncio
from typing import Dict, Any, List
from itertools import chain

class DataFetcher:

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

    # Make request
    async def _make_request_to_dexscreener(self, url: str) -> Dict[str, Any]:
        if self.session is None:
            self.session = aiohttp.ClientSession()
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Error: API returned status code {response.status}")
                    return {}
        except Exception as e:
            print(f"Error making request to {url}: {e}")
            return {}

    # Get token list
    async def fetch_latest_token_profiles(self) -> List[Dict[str, Any]]:
        data = await self._make_request_to_dexscreener("https://api.dexscreener.com/token-profiles/latest/v1")
        return data

    async def fetch_latest_boosted_token(self) -> List[Dict[str, Any]]:
        data = await self._make_request_to_dexscreener("https://api.dexscreener.com/token-boosts/latest/v1")
        return data
    
    async def fetch_top_boosted_token(self) -> List[Dict[str, Any]]:
        data = await self._make_request_to_dexscreener("https://api.dexscreener.com/token-boosts/top/v1")
        return data
    
    # Merge list (unique)
    async def merge_unique_list(self) -> List[Dict[str, Any]]:
        try:
            latest_token = await self.fetch_latest_token_profiles()
            latest_boosts = await self.fetch_latest_boosted_token()
            top_boosts = await self.fetch_top_boosted_token()

            unique_dict = {
                item['tokenAddress']: item
                for item in chain(latest_token, latest_boosts, top_boosts)
            }
            return list(unique_dict.values())
        
        except Exception as e:
            print(f"Error merging token data: {e}")
            return []
    
    # Only solana list
    async def only_solana_list(self) -> List[Dict[str, Any]]:
        unique_list = await self.merge_unique_list()
        return [item for item in unique_list if item.get('chainId') == "solana"]


    # Get token pool
    async def fetch_one_token_pairs(self, chain_id: str, token_address: str) -> List[Dict[str, Any]]:
        data = await self._make_request_to_dexscreener(f"https://api.dexscreener.com/token-pairs/v1/{chain_id}/{token_address}")
        return data

    async def fetch_multiple_token_pairs(self, chain_id: str, token_address: list) -> List[Dict[str, Any]]:
        token_address_str = ",".join(token_address)
        data = await self._make_request_to_dexscreener(f"https://api.dexscreener.com/tokens/v1/{chain_id}/{token_address_str}")
        return data




if __name__ == "__main__":


    async def main():
        async with DataFetcher() as data_fetcher:
            data1 = await data_fetcher.fetch_latest_token_profiles()
            print(type(data1))
            print(len(data1))
            print(data1[0])
            #data = await data_fetcher.fetch_one_token_pairs("base", "0x23dD3Ce6161422622E773E13dAC2781C7f990D45")

    asyncio.run(main())
