import aiohttp
import asyncio
from typing import Dict, Any, List
from itertools import chain

class DexScreenerAPI:

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
    async def _make_request(self, url: str) -> Dict[str, Any]:
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

    async def fetch_latest_token_profiles(self) -> List[Dict[str, Any]]:
        data = await self._make_request("https://api.dexscreener.com/token-profiles/latest/v1")
        return data # Directly return the list

    async def fetch_latest_boosted_token(self) -> List[Dict[str, Any]]:
        data = await self._make_request("https://api.dexscreener.com/token-boosts/latest/v1")
        return data # Directly return the list
    
    async def fetch_top_boosted_token(self) -> List[Dict[str, Any]]:
        data = await self._make_request("https://api.dexscreener.com/token-boosts/top/v1")
        return data # Directly return the list
    
    async def fetch_one_token_pairs(self, chain_id: str, token_address: str) -> List[Dict[str, Any]]:
        data = await self._make_request(f"https://api.dexscreener.com/token-pairs/v1/{chain_id}/{token_address}")
        return data # Directly return the list

    async def fetch_multiple_token_pairs(self, chain_id: str, token_address: list) -> List[Dict[str, Any]]:
        token_address_str = ",".join(token_address)
        data = await self._make_request(f"https://api.dexscreener.com/tokens/v1/{chain_id}/{token_address_str}")
        return data # Directly return the list if API returns a list


    # Process list
    async def merge_unique_token_profiles_list(self) -> List[Dict[str, Any]]:
        try:
            latest_token_profiles = await self.fetch_latest_token_profiles()
            latest_boosts_token_profiles = await self.fetch_latest_boosted_token()
            top_boosts_token_profiles = await self.fetch_top_boosted_token()

            unique_dict = {}
            # Ensure items are dictionaries and have 'tokenAddress'
            for item in chain(latest_token_profiles, latest_boosts_token_profiles, top_boosts_token_profiles):
                 if isinstance(item, dict) and 'tokenAddress' in item:
                    unique_dict[item['tokenAddress']] = item

            return list(unique_dict.values())
        
        except Exception as e:
            print(f"Error merging token data: {e}")
            return []

    async def only_solana_token_profiles_list(self) -> List[Dict[str, Any]]:
        unique_list = await self.merge_unique_token_profiles_list()
        return [item for item in unique_list if item.get('chainId') == "solana"]

    async def only_base_token_profiles_list(self) -> List[Dict[str, Any]]:
        unique_list = await self.merge_unique_token_profiles_list()
        return [item for item in unique_list if item.get('chainId') == "base"]
    
    async def only_bsc_token_profiles_list(self) -> List[Dict[str, Any]]:
        unique_list = await self.merge_unique_token_profiles_list()
        return [item for item in unique_list if item.get('chainId') == "bsc"]


    # Process data for list
    async def fetch_data_for_token_profiles_list(self, profiles_list: List[Dict[str, Any]], chain_id = None) -> List[Dict[str, Any]]:
        
        data_list = []
        if not profiles_list: # Handle empty list
             return data_list

        if chain_id == None:
            tasks = []
            for item in profiles_list:
                # Ensure item has required keys
                if isinstance(item, dict) and 'chainId' in item and 'tokenAddress' in item:
                     tasks.append(self.fetch_one_token_pairs(item['chainId'], item['tokenAddress']))
                else:
                     print(f"Skipping invalid profile item: {item}") # Log invalid items
            results = await asyncio.gather(*tasks)
            # Filter out empty results and flatten
            data_list = [pair for sublist in results if sublist for pair in sublist]

        else:
            address_list = [item['tokenAddress'] for item in profiles_list if isinstance(item, dict) and 'tokenAddress' in item]
            if not address_list: # Handle case where no valid addresses found
                return data_list

            split_address_list = [address_list[i:i+30] for i in range(0, len(address_list), 30)]
            tasks = [
                self.fetch_multiple_token_pairs(chain_id, address_chunk)
                for address_chunk in split_address_list
            ]
            results = await asyncio.gather(*tasks)
            # Filter out empty results and flatten
            data_list = [pair for sublist in results if sublist for pair in sublist]
        
        return data_list


if __name__ == "__main__":
    async def main():
        async with DexScreenerAPI() as data_fetcher:
            token_list = await data_fetcher.merge_unique_token_profiles_list()
            import json
            with open('dex_token_list.json', 'w') as f:
                json.dump(token_list, f, indent=4)
            token_data = await data_fetcher.fetch_data_for_token_profiles_list(token_list)
            with open('dex_token_data.json', 'w') as f:
                json.dump(token_data, f, indent=4)
            # print(raw_token_data)
    asyncio.run(main())
