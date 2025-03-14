import uvicorn
import asyncio
import json
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

from data_fetcher import DataFetcher
from websocket import manager


async def get_full_data(data_fetcher: DataFetcher, username=None):
    """获取完整的数据，包括基础数据和用户收藏（如果有）"""
    solana_token_list = await data_fetcher.only_solana_token_profiles_list()
    solana_token_data = await data_fetcher.fetch_data_for_token_profiles_list(solana_token_list, "solana")
    solana_filtered_data = await data_fetcher.filter_data_for_web(solana_token_list, solana_token_data)
    
    base_token_list = await data_fetcher.only_base_token_profiles_list()
    base_token_data = await data_fetcher.fetch_data_for_token_profiles_list(base_token_list, "base")
    base_filtered_data = await data_fetcher.filter_data_for_web(base_token_list, base_token_data)

    bsc_token_list = await data_fetcher.only_bsc_token_profiles_list()
    bsc_token_data = await data_fetcher.fetch_data_for_token_profiles_list(bsc_token_list, "bsc")
    bsc_filtered_data = await data_fetcher.filter_data_for_web(bsc_token_list, bsc_token_data)

    data = {
        "timestamp": str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        "solana_pool": solana_filtered_data,
        "base_pool": base_filtered_data,
        "bsc_pool": bsc_filtered_data
    }
    
    if username:
        data['favorite_tokens'] = await data_fetcher.fetch_data_for_user_favorite(username)
    
    return data


async def periodic_data_update(time_interval=10):
    while True:
        try:
            for connection in manager.active_connections:
                try:
                    username = getattr(connection, 'username', None)
                    data = await get_full_data(data_fetcher, username)
                    await manager.send_personal_message(data, connection)
                except Exception as e:
                    print(f"Error sending data to connection: {e}")
                    continue
            await asyncio.sleep(time_interval)

        except Exception as e:
            print(f"Error in periodic_data_update: {e}")
            await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    update_task = asyncio.create_task(periodic_data_update())
    yield
    update_task.cancel()
    await data_fetcher.close_session()


app = FastAPI(title="alphaseek", lifespan=lifespan)

# 添加环境变量获取
# 获取环境变量中的端口，Cloud Run 会自动设置 PORT 环境变量
PORT = int(os.getenv("PORT", "8080"))
# 获取允许的前端域名，多个域名用逗号分隔

# 修改 CORS 配置，确保正确处理前端域名
FRONTEND_URLS = os.getenv("FRONTEND_URLS", "*").split(",")
ALLOW_CREDENTIALS = False if "*" in FRONTEND_URLS else True

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_URLS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

data_fetcher = DataFetcher()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print(f"New WebSocket connection attempt from {websocket.client} with headers: {websocket.headers}")
    
    # 添加 CORS 头部处理
    origin = websocket.headers.get("origin", "")
    print(f"Connection origin: {origin}")
    
    # 接受连接前记录更多信息
    try:
        await manager.connect(websocket)
        print(f"WebSocket connection established with {websocket.client}")
        
        # 发送初始连接成功消息
        await websocket.send_json({"type": "connection_established", "message": "WebSocket connection established"})
        
        while True:
            data = await websocket.receive_json()
            print(f"Received WebSocket data: {data}")
            if data.get('type') == 'login':
                manager.set_username(websocket, data['username'])
                user_data = await get_full_data(data_fetcher, data['username'])
                await manager.send_personal_message(user_data, websocket)
            elif data.get('type') == 'request_update':
                username = getattr(websocket, 'username', None)
                data = await get_full_data(data_fetcher, username)
                await manager.send_personal_message(data, websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        print(f"WebSocket connection closed with {websocket.client}")
        manager.disconnect(websocket)

# 加载用户数据
def load_users():
    try:
        with open('user.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading users: {e}")
        return {"users": []}

@app.post("/api/login")
async def login(credentials: dict):
    users = load_users()
    for user in users["users"]:
        if (user["username"] == credentials["username"] and 
            user["password"] == credentials["password"]):
            async with DataFetcher() as fetcher:
                data = await get_full_data(fetcher, user["username"])
                return {
                    "status": "success",
                    "username": user["username"],
                    "data": data
                }
    raise HTTPException(status_code=401, detail="Invalid credentials")

def update_user_favorites(username, token_data):
    """Update user's favorite tokens in user.json"""
    try:
        with open('user.json', 'r') as f:
            data = json.load(f)
        
        # 为每个用户添加 favorites 列表（如果不存在）
        for user in data['users']:
            if 'favorites' not in user:
                user['favorites'] = []
            
            # 找到对应用户并添加收藏
            if user['username'] == username:
                # 检查是否已经存在
                if token_data not in user['favorites']:
                    user['favorites'].append(token_data)
        
        # 写回文件
        with open('user.json', 'w') as f:
            json.dump(data, f, indent=2)
            
        return True
    except Exception as e:
        print(f"Error updating favorites: {e}")
        return False

@app.post("/api/add_favorite")
async def add_favorite(data: dict):
    try:
        username = data.get('username')
        token_data = data.get('tokenData')
        
        if not username or not token_data:
            raise HTTPException(status_code=400, detail="Missing username or token data")
        
        if update_user_favorites(username, {
            'tokenAddress': token_data['tokenAddress'],
            'icon': token_data['icon'],
            'url': token_data['url'],
            'chainId': token_data['chainId']
        }):
            # 返回更新后的完整数据
            async with DataFetcher() as fetcher:
                return {
                    "status": "success",
                    "data": await get_full_data(fetcher, username)
                }
        else:
            raise HTTPException(status_code=500, detail="Failed to update favorites")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def delete_user_favorite(username, token_address):
    """Delete a token from user's favorites"""
    try:
        with open('user.json', 'r') as f:
            data = json.load(f)
        
        for user in data['users']:
            if user['username'] == username:
                # 找到要删除的 token
                user['favorites'] = [
                    fav for fav in user['favorites'] 
                    if fav['tokenAddress'] != token_address
                ]
                break
        
        # 写回文件
        with open('user.json', 'w') as f:
            json.dump(data, f, indent=2)
            
        return True
    except Exception as e:
        print(f"Error deleting favorite: {e}")
        return False

@app.post("/api/delete_favorite")
async def delete_favorite(data: dict):
    try:
        username = data.get('username')
        token_address = data.get('tokenAddress')
        
        if not username or not token_address:
            raise HTTPException(status_code=400, detail="Missing username or token address")
        
        if delete_user_favorite(username, token_address):
            # 返回更新后的完整数据
            async with DataFetcher() as fetcher:
                return {
                    "status": "success",
                    "data": await get_full_data(fetcher, username)
                }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete favorite")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# test api
@app.get("/api/test")
async def test():
    return {"status": "success"}

@app.get("/api/data")
async def get_data():
    """提供轮询数据的接口，作为 WebSocket 的备用方案"""
    try:
        data = await get_full_data(data_fetcher)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0",  # 监听所有 IP
        port=8000,  # 使用环境变量中的端口
        reload=True
    )

    '''
    async def main():
        data = await get_latest_token_data()
        print(data[0])

    asyncio.run(main())
    '''