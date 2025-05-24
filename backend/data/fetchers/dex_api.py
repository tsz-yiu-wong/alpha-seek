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


'''
    async def fetch_data_for_user_favorite(self, username: str) -> List[Dict[str, Any]]:
    
        """获取用户收藏的token数据"""
        try:
            # 从 user.json 获取用户的收藏列表
            with open('user.json', 'r') as f:
                data = json.load(f)
            
            # 查找当前用户
            user_favorites = None
            for user in data['users']:
                if user['username'] == username:
                    user_favorites = user.get('favorites', [])
                    break
            
            if not user_favorites:
                return []

            # 获取收藏的 token 数据 (Assuming Solana for now based on original logic)
            # Consider making chain_id dynamic if favorites can span chains
            data_list = await self.fetch_data_for_token_profiles_list(user_favorites, "solana")

            # Use the normalizer function
            filtered_data = await normalizer.filter_data_for_web(user_favorites, data_list)
            return filtered_data

        except FileNotFoundError:
            print("Error: user.json not found.")
            return []
        except json.JSONDecodeError:
            print("Error: Could not decode user.json.")
            return []
        except Exception as e:
            print(f"Error getting favorite token data: {e}")
            return []

    async def fetch_data_for_user_favorite2(self, username: str) -> List[Dict[str, Any]]:
        """获取用户收藏的token数据并更新状态"""
        try:
            # 从 user.json 获取用户的收藏列表
            try:
                with open('user.json', 'r') as f:
                    data = json.load(f)
            except FileNotFoundError:
                print("Error: user.json not found.")
                return []
            except json.JSONDecodeError:
                print("Error: Could not decode user.json.")
                return []

            # 查找当前用户
            try:
                user_data = next(user for user in data['users'] if user['username'] == username)
            except StopIteration:
                 print(f"User '{username}' not found in user.json.")
                 return [] # User not found

            if not user_data.get('favorites'):
                return [] # No favorites for this user

            # 按链分组收藏的tokens
            chain_tokens = {}
            for favorite in user_data.get('favorites', []): # Ensure favorites exists
                 if isinstance(favorite, dict) and 'chainId' in favorite: # Validate favorite format
                    chain_id = favorite['chainId']
                    if chain_id not in chain_tokens:
                        chain_tokens[chain_id] = []
                    chain_tokens[chain_id].append(favorite)
                 else:
                    print(f"Skipping invalid favorite item for user {username}: {favorite}")


            # 获取每个链的数据并更新状态
            result = []
            needs_update = False # Flag to track if user.json needs saving
            for chain_id, tokens in chain_tokens.items():
                if not tokens: continue # Skip empty token lists for a chain

                try:
                    token_data = await self.fetch_data_for_token_profiles_list(tokens, chain_id)
                    
                    # 创建 tokenAddress 到数据的映射 (using pairAddress for matching based on API response)
                    active_pairs = {}
                    for item in token_data:
                        if isinstance(item, dict) and 'pairAddress' in item and 'baseToken' in item and 'address' in item['baseToken']:
                             # Using baseToken address as it likely corresponds to the favorite tokenAddress
                             active_pairs[item['baseToken']['address']] = item

                    
                    # 更新每个token的状态和数据
                    for favorite in tokens:
                         if not isinstance(favorite, dict) or 'tokenAddress' not in favorite: continue # Skip invalid format

                         token_address = favorite['tokenAddress']
                         current_status = favorite.get('status')
                         current_last_data = favorite.get('lastData')

                         if token_address in active_pairs:
                             # Token活跃，更新数据
                            new_data = active_pairs[token_address]
                            if favorite.get('status') != 'active' or favorite.get('lastData') != new_data:
                                 favorite['status'] = 'active'
                                 favorite['lastData'] = new_data
                                 needs_update = True

                            # Use the normalizer function
                            filtered_list = await normalizer.filter_data_for_web([favorite], [new_data])
                            if filtered_list:
                                result.append(filtered_list[0])
                         else:
                            # Token不活跃
                            if favorite.get('status') != 'inactive':
                                favorite['status'] = 'inactive'
                                needs_update = True

                            if 'lastData' in favorite:
                                # Use the normalizer function with last known data
                                filtered_list = await normalizer.filter_data_for_web([favorite], [favorite['lastData']])
                                if filtered_list:
                                    inactive_data = filtered_list[0]
                                    inactive_data['status'] = 'inactive' # Ensure status is set correctly
                                    result.append(inactive_data)
                            # else: # No last data, token is inactive and we can't display it
                            #    pass
                    
                    
                except Exception as e:
                    print(f"Error fetching/processing data for chain {chain_id}: {e}")
                    continue # Continue with the next chain

            # 保存更新后的用户数据 only if changes were made
            if needs_update:
                try:
                    with open('user.json', 'w') as f:
                        json.dump(data, f, indent=2)
                except IOError as e:
                    print(f"Error writing updated user.json: {e}")


            return result

        except Exception as e:
            print(f"Error getting favorite token data: {e}")
            return []

# Removed filter methods - they are now in normalizer.py
'''

if __name__ == "__main__":
    async def main():
        async with DexScreenerAPI() as data_fetcher:
            token_list = await data_fetcher.only_solana_token_profiles_list()
            raw_token_data = await data_fetcher.fetch_data_for_token_profiles_list(token_list, "solana")
            print(raw_token_data)
    asyncio.run(main())
