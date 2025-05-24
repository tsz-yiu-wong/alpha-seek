from typing import Dict, Any, List

'''
async def filter_data_for_web(profiles_list: List[Dict[str, Any]], data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalizes DexScreener pair data combined with profile data for web display."""
    summary_list = [] 

    # Create a mapping from token address (from profiles) to profile data
    # This assumes profiles_list contains unique token addresses
    profile_map = {profile.get('tokenAddress'): profile for profile in profiles_list if isinstance(profile, dict) and profile.get('tokenAddress')}

    for data in data_list:
        if not isinstance(data, dict): continue # Skip if data item is not a dict

        # Extract base token address from the pair data
        base_token_address = data.get('baseToken', {}).get('address')
        if not base_token_address:
             # Log or handle cases where baseToken address is missing in pair data
             # print(f"Skipping pair data due to missing baseToken address: {data.get('pairAddress')}")
             continue

        # Find the corresponding profile data using the base token address
        token_profile = profile_map.get(base_token_address)

        # If no matching profile found for the pair's base token, skip or handle
        if not token_profile:
            # This can happen if data_list contains pairs not directly requested via profiles_list,
            # or if the profile list provided didn't map correctly.
            # print(f"Skipping pair data, no matching profile found for baseToken: {base_token_address} in pair {data.get('pairAddress')}")
            continue 

        # Proceed with normalization using both data (pair data) and token_profile (profile data)
        summary_data = {
            # From Profile
            'tokenAddress': token_profile.get('tokenAddress'), # Base token address
            'icon': token_profile.get('icon'),
            'url': data.get('url'), # URL often comes from pair data
            'chainId': data.get('chainId'), # Chain ID from pair data
            # From Pair Data
            'pairAddress': data.get('pairAddress'), # Include pair address for reference
            'symbol': data.get('baseToken', {}).get('symbol'),
            'name': data.get('baseToken', {}).get('name'), # Include name if available
            'dexId': data.get('dexId'),
            'priceNative': data.get('priceNative'),
            'priceUsd': data.get('priceUsd'),
            'txns_m5_buy': data.get('txns', {}).get('m5', {}).get('buys'),
            'txns_m5_sell': data.get('txns', {}).get('m5', {}).get('sells'),
            'txns_h1_buy': data.get('txns', {}).get('h1', {}).get('buys'),
            'txns_h1_sell': data.get('txns', {}).get('h1', {}).get('sells'),
            'txns_h6_buy': data.get('txns', {}).get('h6', {}).get('buys'),
            'txns_h6_sell': data.get('txns', {}).get('h6', {}).get('sells'),
            'txns_h24_buy': data.get('txns', {}).get('h24', {}).get('buys'),
            'txns_h24_sell': data.get('txns', {}).get('h24', {}).get('sells'),
            'volume_m5': data.get('volume', {}).get('m5'),
            'volume_h1': data.get('volume', {}).get('h1'),
            'volume_h6': data.get('volume', {}).get('h6'),
            'volume_h24': data.get('volume', {}).get('h24'),
            'priceChange_m5': data.get('priceChange', {}).get('m5'),
            'priceChange_h1': data.get('priceChange', {}).get('h1'),
            'priceChange_h6': data.get('priceChange', {}).get('h6'),
            'priceChange_h24': data.get('priceChange', {}).get('h24'),
            'liquidity_usd': data.get('liquidity', {}).get('usd'),    
            'liquidity_base': data.get('liquidity', {}).get('base'),
            'liquidity_quote': data.get('liquidity', {}).get('quote'),
            'marketCap': data.get('marketCap'), # Include market cap if available
            'pairCreatedAt': data.get('pairCreatedAt'), # Include pair creation time
        }
        # Safely call get_token_tag, handle potential errors if tag logic fails
        try:
            summary_data['tag'] = get_token_tag(summary_data)
        except Exception as e:
            # print(f"Error generating tag for token {summary_data.get('tokenAddress')}: {e}")
            summary_data['tag'] = None # Assign a default tag or None on error

        summary_list.append(summary_data)

    return summary_list
'''

async def normalize_data_for_database(data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalizes DexScreener pair data specifically for database storage."""
    summary_list = []

    for data in data_list:
        if not isinstance(data, dict): continue # Skip if data item is not a dict

        # Extract base token address from the pair data
        base_token_address = data.get('baseToken', {}).get('address')
        if not base_token_address:
             continue # Skip if no base token address

        summary_data = {
            'tokenAddress': base_token_address, # Use base token address as the primary key
            'pairAddress': data.get('pairAddress'),
            'chainId': data.get('chainId'),
            'dexId': data.get('dexId'),
            'priceNative': data.get('priceNative'),
            'priceUsd': data.get('priceUsd'),
            'txns_m5_buy': data.get('txns', {}).get('m5', {}).get('buys'),
            'txns_m5_sell': data.get('txns', {}).get('m5', {}).get('sells'),
            'txns_h1_buy': data.get('txns', {}).get('h1', {}).get('buys'),
            'txns_h1_sell': data.get('txns', {}).get('h1', {}).get('sells'),
            'txns_h6_buy': data.get('txns', {}).get('h6', {}).get('buys'),
            'txns_h6_sell': data.get('txns', {}).get('h6', {}).get('sells'),
            'txns_h24_buy': data.get('txns', {}).get('h24', {}).get('buys'),
            'txns_h24_sell': data.get('txns', {}).get('h24', {}).get('sells'),
            'volume_m5': data.get('volume', {}).get('m5'),
            'volume_h1': data.get('volume', {}).get('h1'),
            'volume_h6': data.get('volume', {}).get('h6'),
            'volume_h24': data.get('volume', {}).get('h24'),
            'priceChange_m5': data.get('priceChange', {}).get('m5'),
            'priceChange_h1': data.get('priceChange', {}).get('h1'),
            'priceChange_h6': data.get('priceChange', {}).get('h6'),
            'priceChange_h24': data.get('priceChange', {}).get('h24'),
            'liquidity_usd': data.get('liquidity', {}).get('usd'),    
            'liquidity_base': data.get('liquidity', {}).get('base'),
            'liquidity_quote': data.get('liquidity', {}).get('quote'),
            'marketCap': data.get('marketCap'),
            'pairCreatedAt': data.get('pairCreatedAt'),
            # Add timestamp of when the data was fetched/normalized
            # 'timestamp': datetime.utcnow()
        }
        summary_list.append(summary_data)

    return summary_list


if __name__ == "__main__":
    from fetchers.dex_api import DexScreenerAPI
    import asyncio
    async def main():
        async with DexScreenerAPI() as data_fetcher:
            token_list = await data_fetcher.only_solana_token_profiles_list()
            raw_token_data = await data_fetcher.fetch_data_for_token_profiles_list(token_list, "solana")
            normalized_data = await normalize_data_for_database(raw_token_data)
            print(normalized_data)
            # 转成json格式并储存到目录下
            import json
            with open('normalized_data.json', 'w') as f:
                json.dump(normalized_data, f, indent=4)
    asyncio.run(main())