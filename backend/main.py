from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from datetime import datetime

from data_fetcher import DataFetcher
from websocket import manager

async def get_list_of_token_pools(token_list, chain_id=None):

    summary_list = []

    if chain_id == None:
        tasks = []
        for item in token_list:
            tasks.append(data_fetcher.fetch_one_token_pairs(item['chainId'], item['tokenAddress']))
        results = await asyncio.gather(*tasks)
        token_pools = [item for sublist in results for item in sublist]

    else:
        address_list = [item['tokenAddress'] for item in token_list]
        split_address_list = [address_list[i:i+30] for i in range(0, len(address_list), 30)]
        tasks = [
            data_fetcher.fetch_multiple_token_pairs(chain_id, address_chunk)
            for address_chunk in split_address_list
        ]
        results = await asyncio.gather(*tasks)
        token_pools = [item for sublist in results for item in sublist]

    for item, token_pool in zip(token_list, token_pools):
        summary_data = {
            'tokenAddress': item.get('tokenAddress', None),
            'icon': item.get('icon', None),
            'url': item.get('url', None),
            'chainId': item.get('chainId', None),
            'dexId': token_pool.get('dexId', None),
            'priceNative': token_pool.get('priceNative', None),
            'priceUsd': token_pool.get('priceUsd', None),
            'txns_m5_buy': token_pool.get('txns', {}).get('m5', {}).get('buys', None),
            'txns_m5_sell': token_pool.get('txns', {}).get('m5', {}).get('sells', None),
            'txns_h1_buy': token_pool.get('txns', {}).get('h1', {}).get('buys', None),
            'txns_h1_sell': token_pool.get('txns', {}).get('h1', {}).get('sells', None),
            'txns_h6_buy': token_pool.get('txns', {}).get('h6', {}).get('buys', None),
            'txns_h6_sell': token_pool.get('txns', {}).get('h6', {}).get('sells', None),
            'txns_h24_buy': token_pool.get('txns', {}).get('h24', {}).get('buys', None),
            'txns_h24_sell': token_pool.get('txns', {}).get('h24', {}).get('sells', None),
            'volume_m5': token_pool.get('volume', {}).get('m5', None),
            'volume_h1': token_pool.get('volume', {}).get('h1', None),
            'volume_h6': token_pool.get('volume', {}).get('h6', None),
            'volume_h24': token_pool.get('volume', {}).get('h24', None),
            'priceChange_m5': token_pool.get('priceChange', {}).get('m5', None),
            'priceChange_h1': token_pool.get('priceChange', {}).get('h1', None),
            'priceChange_h6': token_pool.get('priceChange', {}).get('h6', None),
            'priceChange_h24': token_pool.get('priceChange', {}).get('h24', None),
            'liquidity_usd': token_pool.get('liquidity', {}).get('usd', None),    
            'liquidity_base': token_pool.get('liquidity', {}).get('base', None),
            'liquidity_quote': token_pool.get('liquidity', {}).get('quote', None),
        }
        summary_list.append(summary_data)

    return summary_list

async def get_latest_token_data():
    latest_token_list = await data_fetcher.fetch_latest_token_profiles()
    return await get_list_of_token_pools(latest_token_list)

async def get_latest_boosts_token_data():
    latest_boosts = await data_fetcher.fetch_latest_boosted_token()
    return await get_list_of_token_pools(latest_boosts)

async def get_top_boosts_token_data():
    top_boosts = await data_fetcher.fetch_top_boosted_token()
    return await get_list_of_token_pools(top_boosts)

async def get_solana_pool_data():
    solana_list = await data_fetcher.only_solana_list()
    return await get_list_of_token_pools(solana_list, 'solana')


async def periodic_data_update(time_interval=15):
    while True:
        try:
            
            tasks = [
                get_latest_token_data(),
                get_latest_boosts_token_data(),
                get_top_boosts_token_data(),
                get_solana_pool_data()
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            data = {
                "timestamp": str(datetime.now()),
                "latest_token": results[0] if not isinstance(results[0], Exception) else None,
                "latest_boosts": results[1] if not isinstance(results[1], Exception) else None,
                "top_boosts": results[2] if not isinstance(results[2], Exception) else None,
                "solana_pool": results[3] if not isinstance(results[3], Exception) else None
            }
            
            await manager.broadcast(data)
            await asyncio.sleep(time_interval)

        except Exception as e:
            print(f"Error in periodic_data_broadcast: {e}")
            await asyncio.sleep(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    update_task = asyncio.create_task(periodic_data_update())
    yield
    update_task.cancel()
    await data_fetcher.close_session()

app = FastAPI(title="Meme Coin AI Platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


data_fetcher = DataFetcher()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 

    '''
    async def main():
        data = await get_latest_token_data()
        print(data[0])

    asyncio.run(main())
    '''