import json
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import logging
from supabase import create_client, Client
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from dex_api import DexScreenerAPI
from cmc_api import CoinMarketCapAPI
import os
import asyncio
import http.client as http_client

# 禁用 HTTP request 日志
http_client.HTTPConnection.debuglevel = 0
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('supabase').setLevel(logging.WARNING)

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# InfluxDB配置
INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "token_price")

# Supabase配置
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------- CMC 相关 -----------
def write_cmc_data_to_influxdb(tokens_data):
    if not tokens_data:
        logger.info("[CMC] 写入 InfluxDB：0条")
        return
    # 处理 category list 格式
    if isinstance(tokens_data, dict) and 'coins' in tokens_data:
        tokens_data = tokens_data['coins']
    points = []
    for item in tokens_data:
        try:
            point = Point("token_metrics") \
                .tag("source", "cmc") \
                .tag("token_symbol", item['symbol']) \
                .tag("token_name", item['name'])
            if item.get('platform') is not None:
                point = point \
                    .tag("chain_id", item['platform']['name']) \
                    .tag("token_address", item['platform']['token_address'])
            timestamp_str = item['quote']['USD']['last_updated']
            if timestamp_str.endswith('Z'):
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(timestamp_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt = dt.astimezone(timezone.utc)
            point = point \
                .field("price_usd", float(item['quote']['USD']['price'])) \
                .field("percent_change_1h", float(item['quote']['USD']['percent_change_1h'])) \
                .field("percent_change_24h", float(item['quote']['USD']['percent_change_24h'])) \
                .field("percent_change_7d", float(item['quote']['USD']['percent_change_7d'])) \
                .field("volume_24h", float(item['quote']['USD']['volume_24h'])) \
                .field("volume_change_24h", float(item['quote']['USD']['volume_change_24h'])) \
                .field("market_cap", float(item['quote']['USD']['market_cap'])) \
                .field("market_cap_dominance", float(item['quote']['USD']['market_cap_dominance'])) \
                .time(dt)
            points.append(point)
        except Exception as e:
            logger.error(f"Error processing CMC item {item.get('symbol', 'unknown')}: {str(e)}")
            continue
    if points:
        try:
            with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG) as client:
                write_api = client.write_api(write_options=SYNCHRONOUS)
                write_api.write(bucket=INFLUXDB_BUCKET, record=points)
                logger.info(f"[CMC] 写入 InfluxDB：{len(points)}条")
        except Exception as e:
            logger.error(f"Error writing CMC to InfluxDB: {str(e)}")

# ----------- Dex Screener 相关 -----------
async def upsert_watchlist_to_supabase(token_profiles: list):
    if not token_profiles:
        logger.info("[DexScreener] watchlist 新增：0个")
        return
    
    # 获取现有的 token_address 和 chain_id 组合
    existing_tokens = set()
    try:
        response = supabase.table("token_watchlist").select("token_address, chain_id").execute()
        if response.data:
            for row in response.data:
                if row.get("token_address") and row.get("chain_id"):
                    existing_tokens.add((row["token_address"], row["chain_id"]))
    except Exception as e:
        logger.error(f"Error fetching existing tokens from watchlist: {e}")
        return

    # 准备新代币数据
    new_tokens = []
    current_time = datetime.now(timezone.utc).isoformat()
    for profile in token_profiles:
        if isinstance(profile, dict) and profile.get('tokenAddress') and profile.get('chainId'):
            token_key = (profile['tokenAddress'], profile['chainId'])
            if token_key not in existing_tokens:
                new_tokens.append({
                    "token_address": profile['tokenAddress'],
                    "chain_id": profile['chainId'],
                    "last_updated": current_time,
                    "is_active": True
                })
    
    if new_tokens:
        try:
            supabase.table("token_watchlist").insert(new_tokens).execute()
            logger.info(f"[DexScreener] watchlist 新增：{len(new_tokens)}个")
        except Exception as e:
            logger.error(f"Error inserting new tokens to watchlist: {e}")
    else:
        logger.info("[DexScreener] watchlist 新增：0个")

async def fetch_active_tokens_from_supabase() -> list:
    try:
        response = supabase.table("token_watchlist").select("token_address, chain_id").eq("is_active", True).execute()
        active_tokens = response.data
        logger.info(f"[DexScreener] 从 Supabase 获取到活跃代币：{len(active_tokens) if active_tokens else 0}条")
        return active_tokens or []
    except Exception as e:
        logger.error(f"Error fetching active tokens from Supabase: {e}")
        return []

async def upsert_new_tokens_info_to_supabase(token_details: list):
    if not token_details:
        logger.info("[DexScreener] 写入 token info：0条")
        return
    existing_tokens = set()
    try:
        response = supabase.table("token_info").select("token_address, chain_id").execute()
        if response.data:
            for row in response.data:
                if row.get("token_address") and row.get("chain_id"):
                    existing_tokens.add((row["token_address"], row["chain_id"]))
    except Exception as e:
        logger.error(f"Error fetching existing tokens from token_info: {e}")
        return
    new_token_records = []
    for item in token_details:
        base_token = item.get("baseToken", {})
        quote_token = item.get("quoteToken", {})
        info = item.get("info", {})
        token_address = base_token.get("address")
        chain_id = item.get("chainId")
        if not token_address or not chain_id:
            continue
        if (token_address, chain_id) in existing_tokens:
            continue
        record = {
            "chain_id": chain_id,
            "token_address": token_address,
            "token_name": base_token.get("name"),
            "token_symbol": base_token.get("symbol"),
            "token_icon_url": info.get("imageUrl"),
            "token_websites": info.get("websites", []),
            "token_socials": info.get("socials", []),
            "quote_token_address": quote_token.get("address"),
            "quote_token_name": quote_token.get("name"),
            "quote_token_symbol": quote_token.get("symbol"),
            "dex_id": item.get("dexId"),
            "pair_address": item.get("pairAddress")
        }
        record_cleaned = {k: v for k, v in record.items() if v is not None}
        if "token_address" in record_cleaned and "chain_id" in record_cleaned:
            new_token_records.append(record_cleaned)
    if new_token_records:
        try:
            chunk_size = 100
            for i in range(0, len(new_token_records), chunk_size):
                chunk = new_token_records[i:i+chunk_size]
                supabase.table("token_info").upsert(chunk, on_conflict='token_address,chain_id').execute()
            logger.info(f"[DexScreener] 写入 token info：{len(new_token_records)}条")
        except Exception as e:
            logger.error(f"Error inserting new tokens to token_info: {e}")
    else:
        logger.info("[DexScreener] 写入 token info：0条")

def write_dex_data_to_influxdb(tokens_data: list):
    if not tokens_data:
        logger.info("[DexScreener] 写入 InfluxDB：0条")
        return
    points = []
    current_time = datetime.now(timezone.utc)
    for item in tokens_data:
        try:
            point = Point("token_metrics")\
                .tag("source", "dexscreener")\
                .tag("dex_id", item.get("dexId"))\
                .tag("pair_address", item.get("pairAddress"))\
                .tag("chain_id", item.get("chainId"))\
                .tag("token_address", item.get("baseToken", {}).get("address"))\
                .tag("token_symbol", item.get("baseToken", {}).get("symbol"))\
                .tag("token_name", item.get("baseToken", {}).get("name"))\
                .field("price_native", float(item.get("priceNative", 0)) if item.get("priceNative") is not None else 0.0)\
                .field("price_usd", float(item.get("priceUsd", 0)) if item.get("priceUsd") is not None else 0.0)\
                .field("percent_change_5m", float(item.get("priceChange", {}).get("m5", 0)) if item.get("priceChange", {}).get("m5") is not None else 0.0)\
                .field("percent_change_1h", float(item.get("priceChange", {}).get("h1", 0)) if item.get("priceChange", {}).get("h1") is not None else 0.0)\
                .field("percent_change_6h", float(item.get("priceChange", {}).get("h6", 0)) if item.get("priceChange", {}).get("h6") is not None else 0.0)\
                .field("percent_change_24h", float(item.get("priceChange", {}).get("h24", 0)) if item.get("priceChange", {}).get("h24") is not None else 0.0)\
                .field("txns_buys_5m", int(item.get("txns", {}).get("m5", {}).get("buys", 0)))\
                .field("txns_sells_5m", int(item.get("txns", {}).get("m5", {}).get("sells", 0)))\
                .field("txns_buys_1h", int(item.get("txns", {}).get("h1", {}).get("buys", 0)))\
                .field("txns_sells_1h", int(item.get("txns", {}).get("h1", {}).get("sells", 0)))\
                .field("txns_buys_6h", int(item.get("txns", {}).get("h6", {}).get("buys", 0)))\
                .field("txns_sells_6h", int(item.get("txns", {}).get("h6", {}).get("sells", 0)))\
                .field("txns_buys_24h", int(item.get("txns", {}).get("h24", {}).get("buys", 0)))\
                .field("txns_sells_24h", int(item.get("txns", {}).get("h24", {}).get("sells", 0)))\
                .field("volume_5m", float(item.get("volume", {}).get("m5", 0)) if item.get("volume", {}).get("m5") is not None else 0.0)\
                .field("volume_1h", float(item.get("volume", {}).get("h1", 0)) if item.get("volume", {}).get("h1") is not None else 0.0)\
                .field("volume_6h", float(item.get("volume", {}).get("h6", 0)) if item.get("volume", {}).get("h6") is not None else 0.0)\
                .field("volume_24h", float(item.get("volume", {}).get("h24", 0)) if item.get("volume", {}).get("h24") is not None else 0.0)\
                .field("liquidity_usd", float(item.get("liquidity", {}).get("usd", 0)) if item.get("liquidity", {}).get("usd") is not None else 0.0)\
                .field("liquidity_base", float(item.get("liquidity", {}).get("base", 0)) if item.get("liquidity", {}).get("base") is not None else 0.0)\
                .field("liquidity_quote", float(item.get("liquidity", {}).get("quote", 0)) if item.get("liquidity", {}).get("quote") is not None else 0.0)\
                .field("market_cap", float(item.get("fdv", 0)) if item.get("fdv") is not None else 0.0)\
                .time(current_time)
            points.append(point)
        except Exception as e:
            logger.error(f"Error processing DEX item for InfluxDB: {item.get('pairAddress', 'unknown pair')} - {e}")
            continue
    if points:
        try:
            with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG) as client:
                write_api = client.write_api(write_options=SYNCHRONOUS)
                write_api.write(bucket=INFLUXDB_BUCKET, record=points)
                logger.info(f"[DexScreener] 写入 InfluxDB：{len(points)}条")
        except Exception as e:
            logger.error(f"Error writing DEX data to InfluxDB: {e}")

async def deactivate_tokens_in_supabase(token_details: list):
    if not token_details:
        logger.info("[DexScreener] 无需下架任何代币")
        return
    tokens_to_deactivate = []
    current_time = datetime.now(timezone.utc).isoformat()
    for item in token_details:
        price_change_24h = item.get("priceChange", {}).get("h24")
        base_token = item.get("baseToken", {})
        token_address = base_token.get("address")
        chain_id = item.get("chainId")
        if price_change_24h is not None and token_address and chain_id:
            try:
                if float(price_change_24h) < -80:
                    tokens_to_deactivate.append({
                        "token_address": token_address,
                        "chain_id": chain_id,
                        "is_active": False,
                        "last_updated": current_time
                    })
            except Exception as e:
                logger.warning(f"Could not parse price_change_24h: {price_change_24h} for token {token_address}: {e}")
    if tokens_to_deactivate:
        try:
            supabase.table("token_watchlist").upsert(tokens_to_deactivate, on_conflict='token_address,chain_id').execute()
            logger.info(f"[DexScreener] 下架代币：{len(tokens_to_deactivate)}个")
        except Exception as e:
            logger.error(f"Error deactivating tokens in Supabase: {e}")
    else:
        logger.info("[DexScreener] 无需下架任何代币")

# ----------- 主流程 -----------
async def process_dex_screener_data():
    async with DexScreenerAPI() as dex_api:
        # 1. 获取最新token address和chain_id
        token_profiles = await dex_api.merge_unique_token_profiles_list()
        logger.info(f"[DexScreener] 获取到热门代币：{len(token_profiles)}条")
        # 2. upsert到watchlist
        await upsert_watchlist_to_supabase(token_profiles)
        # 3. 获取active token
        active_tokens = await fetch_active_tokens_from_supabase()
        if not active_tokens:
            return
        # 3.1 修正字段名，转换为fetch_data_for_token_profiles_list需要的格式
        token_profiles_for_fetch = [
            {"tokenAddress": t["token_address"], "chainId": t["chain_id"]}
            for t in active_tokens
            if t.get("token_address") and t.get("chain_id")
        ]
        # 4. 获取详细token信息（pair数据，可能有重复token）
        token_details = await dex_api.fetch_data_for_token_profiles_list(token_profiles_for_fetch)
        logger.info(f"[DexScreener] 获取到交易对数据：{len(token_details)}条")
        # 4.1 只保留每个token_address+chain_id liquidity_usd最高的pair
        best_pair_per_token = {}
        for item in token_details:
            base_token = item.get("baseToken", {})
            token_address = base_token.get("address")
            chain_id = item.get("chainId")
            liquidity = float(item.get("liquidity", {}).get("usd", 0) or 0)
            if not token_address or not chain_id:
                continue
            key = (token_address, chain_id)
            if key not in best_pair_per_token or liquidity > best_pair_per_token[key][1]:
                best_pair_per_token[key] = (item, liquidity)
        final_token_details = [v[0] for v in best_pair_per_token.values()]
        logger.info(f"[DexScreener] 筛选后唯一代币数：{len(final_token_details)}条")
        if not final_token_details:
            return
        # 5. upsert新token info
        await upsert_new_tokens_info_to_supabase(final_token_details)
        # 6. 处理下架逻辑
        await deactivate_tokens_in_supabase(final_token_details)
        # 7. 写入InfluxDB
        write_dex_data_to_influxdb(final_token_details)

async def main():
    try:
        async with CoinMarketCapAPI() as cmc_api, DexScreenerAPI() as dex_api:
            # 创建 CMC 和 DexScreener 的任务
            cmc_tasks = [
                cmc_api.get_latest_listings(),
                cmc_api.get_category_listings("Binance Alpha")
            ]
            
            # 执行 DexScreener 数据获取
            await process_dex_screener_data()
            
            # 处理 CMC 结果
            cmc_results = await asyncio.gather(*cmc_tasks)
            latest_data, trending_data = cmc_results
            logger.info(f"[CMC] 获取到最新代币：{len(latest_data) if latest_data else 0}条")
            write_cmc_data_to_influxdb(latest_data)
            logger.info(f"[CMC] 获取到Binance Alpha代币：{len(trending_data.get('coins')) if trending_data else 0}条")
            write_cmc_data_to_influxdb(trending_data)
            
    except Exception as e:
        logger.error(f"Error in data processing: {str(e)}")
        raise  # 抛出异常，让 Cloud Run Job 知道执行失败

if __name__ == "__main__":
    required_env_vars = ["INFLUXDB_URL", "INFLUXDB_TOKEN", "INFLUXDB_ORG", "SUPABASE_URL", "SUPABASE_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    else:
        asyncio.run(main())