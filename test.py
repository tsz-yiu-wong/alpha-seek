import requests
import time
from itertools import chain


response = requests.get(
    "https://api.dexscreener.com/token-profiles/latest/v1",
    headers={},
)
latest_token = response.json()
print("len(latest_token): ",len(latest_token))
print(latest_token[0]['url'])
print(latest_token[1]['url'])
print(latest_token[2]['url'])


response = requests.get(
    "https://api.dexscreener.com/token-boosts/latest/v1",
    headers={},
)
latest_boosts = response.json()
print("len(latest_boosts): ",len(latest_boosts))
print(latest_boosts[0]['url'])
print(latest_boosts[1]['url'])
print(latest_boosts[2]['url'])

response = requests.get(
    "https://api.dexscreener.com/token-boosts/top/v1",
    headers={},
)

top_boosts = response.json()
print("len(top_boosts): ",len(top_boosts))
print(top_boosts[0]['url'])
print(top_boosts[1]['url'])
print(top_boosts[2]['url'])


unique_dict = {
    item['tokenAddress']: item
    for item in chain(latest_token, latest_boosts, top_boosts)
}
merged_list = list(unique_dict.values())
print("len(merged_list): ",len(merged_list))
print(merged_list[0]['url'])
print(merged_list[1]['url'])
print(merged_list[2]['url'])


solana_list = [item for item in merged_list if item.get('chainId') == "solana"]
print("len(solana_list): ",len(solana_list))
print(solana_list[0]['url'])
print(solana_list[1]['url'])
print(solana_list[2]['url'])



'''
print("=" * 50)
print(f"Total tokens: {len(data)}")

print("=" * 50)
for token in data:

    print("url: ",token['url'])
print("=" * 50)
print("Token details:")
print("=" * 50)
for key,value in data[0].items():
    print(f"[{key}] = {value}")
print("=" * 50)
'''

# 获取token pairs
chain_id = solana_list[0]['chainId']
token_address = solana_list[0]['tokenAddress']
response = requests.get(
        f"https://api.dexscreener.com/token-pairs/v1/{chain_id}/{token_address}",
        headers={},
    )

data = response.json()

print(data)

'''

response = requests.get(
    f"https://api.dexscreener.com/tokens/v1/{chain_id}/{token_address}",
    headers={},
)
data = response.json()

print(type(data))


print("Token pairs:")
print("=" * 50)
for key,value in data[0].items():
    print(f"[{key}] = {value}")
print("=" * 50)

# 获取实时token prices
print("Token prices:")
print("=" * 50)
for i in range(60):
    response = requests.get(
        f"https://api.dexscreener.com/token-pairs/v1/{chain_id}/{token_address}",
        headers={},
    )
    data = response.json()
    print(f"{i}: {data[0]['priceUsd']}")
    time.sleep(1)
'''