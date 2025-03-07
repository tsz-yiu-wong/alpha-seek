import aiohttp
import asyncio
import json
from typing import Dict, Any, List
from itertools import chain

from strategy import get_token_tag

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

    async def close_session(self):
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None


    # Call API
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

    async def fetch_latest_token_profiles(self) -> List[Dict[str, Any]]:
        data = await self._make_request_to_dexscreener("https://api.dexscreener.com/token-profiles/latest/v1")
        return data

    async def fetch_latest_boosted_token(self) -> List[Dict[str, Any]]:
        data = await self._make_request_to_dexscreener("https://api.dexscreener.com/token-boosts/latest/v1")
        return data
    
    async def fetch_top_boosted_token(self) -> List[Dict[str, Any]]:
        data = await self._make_request_to_dexscreener("https://api.dexscreener.com/token-boosts/top/v1")
        return data
    
    async def fetch_one_token_pairs(self, chain_id: str, token_address: str) -> List[Dict[str, Any]]:
        data = await self._make_request_to_dexscreener(f"https://api.dexscreener.com/token-pairs/v1/{chain_id}/{token_address}")
        return data

    async def fetch_multiple_token_pairs(self, chain_id: str, token_address: list) -> List[Dict[str, Any]]:
        token_address_str = ",".join(token_address)
        data = await self._make_request_to_dexscreener(f"https://api.dexscreener.com/tokens/v1/{chain_id}/{token_address_str}")
        return data


    # Process list
    async def merge_unique_token_profiles_list(self) -> List[Dict[str, Any]]:
        try:
            latest_token_profiles = await self.fetch_latest_token_profiles()
            latest_boosts_token_profiles = await self.fetch_latest_boosted_token()
            top_boosts_token_profiles = await self.fetch_top_boosted_token()

            unique_dict = {
                item['tokenAddress']: item
                for item in chain(latest_token_profiles, latest_boosts_token_profiles, top_boosts_token_profiles)
            }
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
        
        if chain_id == None:
            tasks = []
            for item in profiles_list:
                tasks.append(self.fetch_one_token_pairs(item['chainId'], item['tokenAddress']))
            results = await asyncio.gather(*tasks)
            data_list = [item for sublist in results for item in sublist]
        
        else:
            address_list = [item['tokenAddress'] for item in profiles_list]
            split_address_list = [address_list[i:i+30] for i in range(0, len(address_list), 30)]
            tasks = [
                self.fetch_multiple_token_pairs(chain_id, address_chunk)
                for address_chunk in split_address_list
            ]
            results = await asyncio.gather(*tasks)
            data_list = [item for sublist in results for item in sublist]
        
        return data_list

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

            # 获取收藏的 token 数据
            data_list = await self.fetch_data_for_token_profiles_list(user_favorites, "solana")
            filtered_data = await self.filter_data_for_web(user_favorites, data_list)
            return filtered_data

        except Exception as e:
            print(f"Error getting favorite token data: {e}")
            return []


    async def fetch_data_for_user_favorite2(self, username: str) -> List[Dict[str, Any]]:
        """获取用户收藏的token数据并更新状态"""
        try:
            # 从 user.json 获取用户的收藏列表
            with open('user.json', 'r') as f:
                data = json.load(f)
            
            # 查找当前用户
            try:
                user_data = next(user for user in data['users'] if user['username'] == username)
            except StopIteration:
                return []

            if not user_data.get('favorites'):
                return []

            # 按链分组收藏的tokens
            chain_tokens = {}
            for favorite in user_data['favorites']:
                chain_id = favorite['chainId']
                if chain_id not in chain_tokens:
                    chain_tokens[chain_id] = []
                chain_tokens[chain_id].append(favorite)

            # 获取每个链的数据并更新状态
            result = []
            for chain_id, tokens in chain_tokens.items():
                try:
                    token_data = await self.fetch_data_for_token_profiles_list(tokens, chain_id)
                    print("type(token_data):", type(token_data))
                    print("len(token_data):", len(token_data))
                    print("token_data[0]:", token_data[0])
                    
                    # 创建 tokenAddress 到数据的映射
                    active_tokens = {item['tokenAddress']: item for item in token_data if 'tokenAddress' in item}
                    
                    # 更新每个token的状态和数据
                    for favorite in tokens:
                        token_address = favorite['tokenAddress']
                        if token_address in active_tokens:
                            # Token活跃，更新数据
                            favorite['status'] = 'active'
                            favorite['lastData'] = active_tokens[token_address]
                            filtered_data = await self.filter_data_for_web([favorite], [active_tokens[token_address]])
                            if filtered_data:
                                result.append(filtered_data[0])
                        else:
                            # Token不活跃
                            favorite['status'] = 'inactive'
                            if 'lastData' in favorite:
                                # 使用上次的数据，但标记为不活跃
                                filtered_data = await self.filter_data_for_web([favorite], [favorite['lastData']])
                                if filtered_data:
                                    inactive_data = filtered_data[0]
                                    inactive_data['status'] = 'inactive'
                                    result.append(inactive_data)
                    
                    # 保存更新后的用户数据
                    with open('user.json', 'w') as f:
                        json.dump(data, f, indent=2)
                    
                except Exception as e:
                    print(f"Error fetching data for chain {chain_id}: {e}")
                    continue

            return result

        except Exception as e:
            print(f"Error getting favorite token data: {e}")
            return []


    # Filter data
    async def filter_data_for_web(self, profiles_list: List[Dict[str, Any]], data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        
        summary_list = []

        for token, data in zip(profiles_list, data_list):
            summary_data = {
                'tokenAddress': token.get('tokenAddress', None),
                'icon': token.get('icon', None),
                'url': token.get('url', None),
                'chainId': token.get('chainId', None),
                'symbol': data.get('baseToken', {}).get('symbol', None),
                'dexId': data.get('dexId', None),
                'priceNative': data.get('priceNative', None),
                'priceUsd': data.get('priceUsd', None),
                'txns_m5_buy': data.get('txns', {}).get('m5', {}).get('buys', None),
                'txns_m5_sell': data.get('txns', {}).get('m5', {}).get('sells', None),
                'txns_h1_buy': data.get('txns', {}).get('h1', {}).get('buys', None),
                'txns_h1_sell': data.get('txns', {}).get('h1', {}).get('sells', None),
                'txns_h6_buy': data.get('txns', {}).get('h6', {}).get('buys', None),
                'txns_h6_sell': data.get('txns', {}).get('h6', {}).get('sells', None),
                'txns_h24_buy': data.get('txns', {}).get('h24', {}).get('buys', None),
                'txns_h24_sell': data.get('txns', {}).get('h24', {}).get('sells', None),
                'volume_m5': data.get('volume', {}).get('m5', None),
                'volume_h1': data.get('volume', {}).get('h1', None),
                'volume_h6': data.get('volume', {}).get('h6', None),
                'volume_h24': data.get('volume', {}).get('h24', None),
                'priceChange_m5': data.get('priceChange', {}).get('m5', None),
                'priceChange_h1': data.get('priceChange', {}).get('h1', None),
                'priceChange_h6': data.get('priceChange', {}).get('h6', None),
                'priceChange_h24': data.get('priceChange', {}).get('h24', None),
                'liquidity_usd': data.get('liquidity', {}).get('usd', None),    
                'liquidity_base': data.get('liquidity', {}).get('base', None),
                'liquidity_quote': data.get('liquidity', {}).get('quote', None),
            }
            summary_data['tag'] = get_token_tag(summary_data)
            summary_list.append(summary_data)

        return summary_list
    
    async def filter_data_for_database(self, profiles_list: List[Dict[str, Any]], data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        
        summary_list = []

        for token, data in zip(profiles_list, data_list):
            summary_data = {
                'tokenAddress': token.get('tokenAddress', None),
                'chainId': token.get('chainId', None),
                'priceNative': data.get('priceNative', None),
                'priceUsd': data.get('priceUsd', None),
                'txns_m5_buy': data.get('txns', {}).get('m5', {}).get('buys', None),
                'txns_m5_sell': data.get('txns', {}).get('m5', {}).get('sells', None),
                'txns_h1_buy': data.get('txns', {}).get('h1', {}).get('buys', None),
                'txns_h1_sell': data.get('txns', {}).get('h1', {}).get('sells', None),
                'txns_h6_buy': data.get('txns', {}).get('h6', {}).get('buys', None),
                'txns_h6_sell': data.get('txns', {}).get('h6', {}).get('sells', None),
                'txns_h24_buy': data.get('txns', {}).get('h24', {}).get('buys', None),
                'txns_h24_sell': data.get('txns', {}).get('h24', {}).get('sells', None),
                'volume_m5': data.get('volume', {}).get('m5', None),
                'volume_h1': data.get('volume', {}).get('h1', None),
                'volume_h6': data.get('volume', {}).get('h6', None),
                'volume_h24': data.get('volume', {}).get('h24', None),
                'priceChange_m5': data.get('priceChange', {}).get('m5', None),
                'priceChange_h1': data.get('priceChange', {}).get('h1', None),
                'priceChange_h6': data.get('priceChange', {}).get('h6', None),
                'priceChange_h24': data.get('priceChange', {}).get('h24', None),
                'liquidity_usd': data.get('liquidity', {}).get('usd', None),    
                'liquidity_base': data.get('liquidity', {}).get('base', None),
                'liquidity_quote': data.get('liquidity', {}).get('quote', None),
            }
            summary_list.append(summary_data)

        return summary_list
            



if __name__ == "__main__":

    async def main():
        async with DataFetcher() as data_fetcher:
            '''
            profiles_list = await data_fetcher.only_solana_token_profiles_list()
            data_list = await data_fetcher.fetch_data_for_token_profiles_list(profiles_list, "solana")
            data = await data_fetcher.filter_data_for_web(profiles_list, data_list)
            print("type(data):", type(data))
            print("len(data):", len(data))
            '''
            #token_list2 = await data_fetcher.fetch_data_for_user_favorite("admin")
            #print("token_list2[0]:", token_list2[0])

            token_list3 = await data_fetcher.only_bsc_token_profiles_list()
            print("token_list3[0]:", token_list3[0])

    asyncio.run(main())
