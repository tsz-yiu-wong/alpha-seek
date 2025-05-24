from solders.keypair import Keypair
from solana.rpc.api import Client
from solders.pubkey import Pubkey as PublicKey
import bip39
import json
import os
import secrets

RPC_URL = "https://api.mainnet-beta.solana.com"
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')

def create_random_wallet():
    """创建随机钱包"""
    # 生成32字节的随机种子
    seed = secrets.token_bytes(32)
    kp = Keypair.from_seed(seed)
    return kp

def create_wallet_from_mnemonic(mnemonic: str):
    """从助记词创建钱包"""
    seed = bip39.mnemonic_to_seed(mnemonic)
    kp = Keypair.from_seed(seed[:32])  # 使用前32字节作为种子
    return kp

def save_wallet_to_config(wallet: Keypair, wallet_type: str = "random"):
    """保存钱包信息到配置文件"""
    wallet_info = {
        "public_key": str(wallet.pubkey()),
        "private_key": bytes(wallet).hex(),  # 使用 bytes() 获取私钥
        "type": wallet_type
    }
    
    config_data = {"solana_wallets": []}  # 默认包含空的钱包数组
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            try:
                config_data = json.load(f)
                if "solana_wallets" not in config_data:
                    config_data["solana_wallets"] = []
            except json.JSONDecodeError:
                config_data = {"solana_wallets": []}
    
    # 添加新钱包到数组
    config_data["solana_wallets"].append(wallet_info)
    
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config_data, f, indent=2)


def load_wallet(private_key_hex: str):
    kp = Keypair.from_bytes(bytes.fromhex(private_key_hex))
    return kp

def get_balance(pubkey: PublicKey, client: Client):
    """获取钱包余额"""
    resp = client.get_balance(pubkey)
    balance = resp.value / 1e9  # 转换为 SOL
    return balance

if __name__ == "__main__":
    # 创建随机钱包
    #random_wallet = create_random_wallet()
    #save_wallet_to_config(random_wallet, "random")
    #print(f"随机钱包已保存到 {CONFIG_PATH}")

    # 查询config.json中的所有钱包余额
    with open(CONFIG_PATH, 'r') as f:
        config_data = json.load(f)
        client = Client(RPC_URL)
        
        for wallet_info in config_data.get("solana_wallets", []):
            wallet = load_wallet(wallet_info["private_key"])
            balance = get_balance(wallet.pubkey(), client)
            print(f"钱包公钥: {wallet.pubkey()}")
            print(f"钱包类型: {wallet_info['type']}")
            print(f"钱包余额: {balance} SOL")
            print("-" * 50)
