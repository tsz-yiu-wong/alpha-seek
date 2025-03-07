import os, time
import asyncio

from influxdb_client_3 import InfluxDBClient3, Point
from dotenv import load_dotenv

from data_fetcher import DataFetcher


load_dotenv()

def connect_to_database():
    host = os.getenv("INFLUXDB_URL")
    token = os.getenv("INFLUXDB_TOKEN")
    org = os.getenv("INFLUXDB_ORG")
    database = "TEST"

    client = InfluxDBClient3(host=host, token=token, org=org, database=database)
    return client

def get_data_from_database(query):
    client = connect_to_database()
    result = client.query(query)
    print(result)
    client.close()

async def write_token_data(data_list):
    client = connect_to_database()
    
    try:
        points = []
        for item in data_list:
            if not item.get('tokenAddress') or not item.get('chainId'):
                print(f"Skipping record due to missing required tags: {item}")
                continue
                
            point = Point("token_data") \
                .tag("tokenAddress", item['tokenAddress']) \
                .tag("chainId", item['chainId'])
            
            for key, value in item.items():
                if key not in ['tokenAddress', 'chainId'] and value is not None:
                    try:
                        # 强制转换所有数值为 float64
                        if isinstance(value, (int, float, str)):
                            value = float(value)  # 统一转换为 float64
                        point = point.field(key, value)
                    except (ValueError, TypeError) as e:
                        print(f"Skipping field {key} due to invalid value: {value}")
                        continue
            
            points.append(point)

        if points:
            client.write(points)
            print(f"Successfully wrote {len(points)} points to database")
        else:
            print("No valid points to write")
        
    except Exception as e:
        print(f"Error writing to database: {e}")
    finally:
        client.close()

async def period_write_data(time_interval=30):
    while True:
        async with DataFetcher() as data_fetcher:
            token_list = await data_fetcher.only_solana_list()
            token_data = await data_fetcher.fetch_data_for_list(token_list, "solana")
            data = await data_fetcher.filter_data_for_database(token_list, token_data)
            await write_token_data(data)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] write data to database")
        await asyncio.sleep(time_interval)

if __name__ == "__main__":
    async def main():
        await period_write_data()
    asyncio.run(main())
