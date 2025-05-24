import requests
import base64
import time
import asyncio # Needed for async sleep
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.transaction import Transaction
from solders.pubkey import Pubkey
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price # For priority fee

from .solana_wallet import load_wallet, get_balance

RPC_URL = "https://api.mainnet-beta.solana.com"
# Define SOL mint address as a constant
SOL_MINT_ADDRESS = "So11111111111111111111111111111111111111112"
JUPITER_QUOTE_API_URL = "https://quote-api.jup.ag/v6/quote"
JUPITER_SWAP_API_URL = "https://quote-api.jup.ag/v6/swap"

# Removed should_buy function as decision logic is now in strategies

async def get_jupiter_quote(input_mint: str, output_mint: str, amount: int, slippage_bps: int = 50) -> dict | None:
    """获取 Jupiter V6 API 的交易报价"""
    params = {
        "inputMint": input_mint,
        "outputMint": output_mint,
        "amount": amount, # Amount in lamports or smallest token unit
        "slippageBps": slippage_bps, # Slippage basis points (1 bps = 0.01%)
        # "onlyDirectRoutes": True, # Optional: Faster quotes, potentially worse price
        # "asLegacyTransaction": False, # Use VersionedTransaction
    }
    try:
        async with requests.Session() as session:
             # Use asyncio.to_thread if requests doesn't support async directly
             # For simplicity, using sync requests here, but async is better
             # response = await asyncio.to_thread(session.get, JUPITER_QUOTE_API_URL, params=params)
             response = requests.get(JUPITER_QUOTE_API_URL, params=params)
             response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
             quote_response = response.json()
             # print(f"[Jupiter] Quote received: {quote_response}") # Debugging
             return quote_response
    except requests.exceptions.RequestException as e:
        print(f"[Jupiter] Error getting quote: {e}")
        return None
    except Exception as e:
        print(f"[Jupiter] Unexpected error during quote: {e}")
        return None


async def get_jupiter_swap_transaction(wallet_address: str, quote_response: dict) -> dict | None:
     """获取 Jupiter V6 API 的交换交易信息"""
     payload = {
         "quoteResponse": quote_response,
         "userPublicKey": wallet_address,
         "wrapAndUnwrapSol": True, # Automatically wrap/unwrap SOL
         # "asLegacyTransaction": False, # Use VersionedTransaction by default
         # Add priority fee details if desired
         # "computeUnitPriceMicroLamports": 10000 # Example priority fee
     }
     headers = {
         'Content-Type': 'application/json'
     }
     try:
         async with requests.Session() as session:
             # response = await asyncio.to_thread(session.post, JUPITER_SWAP_API_URL, json=payload, headers=headers)
             response = requests.post(JUPITER_SWAP_API_URL, json=payload, headers=headers)
             response.raise_for_status()
             swap_response = response.json()
             # print(f"[Jupiter] Swap transaction received: {swap_response}") # Debugging
             return swap_response
     except requests.exceptions.RequestException as e:
         print(f"[Jupiter] Error getting swap transaction: {e}")
         return None
     except Exception as e:
         print(f"[Jupiter] Unexpected error during swap transaction fetch: {e}")
         return None


async def send_and_confirm_transaction(tx_base64: str, client: Client, wallet: Keypair) -> str | None:
    """发送签名交易并等待确认"""
    try:
        tx_bytes = base64.b64decode(tx_base64)
        # Deserialize as VersionedTransaction (Jupiter V6 default)
        # Note: This requires solana-py >= 0.30.0 and solders >= 0.15.0
        # If using older versions, you might need to handle legacy transactions
        # from solders.transaction import VersionedTransaction
        # try:
        #     tx = VersionedTransaction.from_bytes(tx_bytes)
        # except Exception as e_vtx:
        #     print(f"Failed to decode as VersionedTransaction ({e_vtx}), trying Legacy...")
        #     tx = Transaction.from_bytes(tx_bytes)

        # Simplified: Assume legacy for broad compatibility or ensure Jupiter uses legacy
        # If using `asLegacyTransaction: True` in quote/swap, use Transaction.deserialize
        tx = Transaction.deserialize(tx_bytes)

        # Get latest blockhash
        blockhash_resp = await asyncio.to_thread(client.get_latest_blockhash)
        if not blockhash_resp.value:
             print("[Solana] Failed to get recent blockhash")
             return None
        tx.recent_blockhash = blockhash_resp.value.blockhash

        # Sign the transaction
        tx.sign([wallet]) # Sign with the wallet keypair

        # Serialize and send
        serialized_tx = tx.serialize()
        send_resp = await asyncio.to_thread(client.send_raw_transaction, serialized_tx)
        txid = send_resp.value
        print(f"[Solana] Transaction sent: {txid}")

        # Confirm transaction
        print(f"[Solana] Waiting for confirmation for {txid}...")
        await asyncio.sleep(5) # Initial wait before polling
        confirmed = False
        for _ in range(20): # Poll for ~100 seconds (20 * 5s)
            try:
                status_resp = await asyncio.to_thread(client.get_signature_statuses, [txid])
                if status_resp.value and status_resp.value[0] is not None:
                    status = status_resp.value[0]
                    if status.confirmation_status == "confirmed" or status.confirmation_status == "finalized":
                        print(f"[Solana] Transaction {txid} confirmed ({status.confirmation_status})")
                        confirmed = True
                        break
            except Exception as e:
                print(f"[Solana] Error checking status for {txid}: {e}")
            await asyncio.sleep(5)

        if confirmed:
            return str(txid)
        else:
            print(f"[Solana] Transaction {txid} not confirmed after timeout.")
            return None

    except Exception as e:
        print(f"[Solana] Error sending/confirming transaction: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def perform_swap(wallet: Keypair, client: Client, input_mint: str, output_mint: str, amount: int, slippage_bps: int = 50) -> str | None:
    """
    执行通用的 Jupiter Swap 操作。

    :param wallet: 已加载的钱包 Keypair 对象
    :param client: Solana Client 对象
    :param input_mint: 输入代币的 mint 地址
    :param output_mint: 输出代币的 mint 地址
    :param amount: 输入代币的数量 (以 lamports 或最小单位计)
    :param slippage_bps: 滑点容忍度 (基点, 1 bps = 0.01%)
    :return: 交易 ID 或 None
    """
    try:
        start_time = time.time()
        print(f"[Swap] Starting swap: {amount} units of {input_mint} -> {output_mint}")

        # 1. 获取报价
        print("[Swap] Getting quote...")
        quote_response = await get_jupiter_quote(input_mint, output_mint, amount, slippage_bps)
        if not quote_response:
            print("[Swap] Failed to get quote.")
            return None
        print(f"[Swap] Quote received in {time.time() - start_time:.2f}s. Out amount: {quote_response.get('outAmount')}")

        # 2. 获取交换交易
        print("[Swap] Getting swap transaction...")
        swap_response = await get_jupiter_swap_transaction(str(wallet.pubkey()), quote_response)
        if not swap_response or 'swapTransaction' not in swap_response:
            print("[Swap] Failed to get swap transaction.")
            return None
        swap_tx_base64 = swap_response['swapTransaction']
        print(f"[Swap] Swap transaction received in {time.time() - start_time:.2f}s.")

        # 3. 发送并确认交易
        print("[Swap] Sending and confirming transaction...")
        txid = await send_and_confirm_transaction(swap_tx_base64, client, wallet)

        if txid:
            print(f"[Swap] Swap successful in {time.time() - start_time:.2f}s! Transaction ID: {txid}")
            return txid
        else:
            print(f"[Swap] Swap failed or timed out after {time.time() - start_time:.2f}s.")
            return None

    except Exception as e:
        print(f"[Swap] Swap failed due to unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# --- 移除旧的 execute_trade 和 main --- #
# execute_trade 被 perform_swap 取代
# if __name__ == "__main__": ... 部分移除，因为现在由 trader.py 调用

# 示例：可以保留一个用于直接测试 swap 的 main 函数（如果需要）
async def main_test():
    print("Testing Solana Swap...")
    try:
        # 使用第一个钱包进行测试 (SOL -> USDC)
        wallet_index = 0
        wallet = load_wallet(wallet_index)
        client = Client(RPC_URL)
        print(f"Using wallet: {wallet.pubkey()}")

        # 检查余额
        balance = await asyncio.to_thread(get_balance, wallet.pubkey(), client)
        print(f"Wallet balance: {balance} SOL")
        min_sol_needed = 0.001 # 假设我们要买 0.001 SOL 的 USDC
        if balance < min_sol_needed:
             print(f"Insufficient balance for test swap (need {min_sol_needed} SOL).")
             return

        # 准备参数 (买入 0.001 SOL 的 USDC)
        input_mint = SOL_MINT_ADDRESS
        output_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" # USDC mint
        amount_lamports = int(min_sol_needed * 1e9)
        slippage_bps = 50 # 0.5%

        # 执行 swap
        txid = await perform_swap(
            wallet=wallet,
            client=client,
            input_mint=input_mint,
            output_mint=output_mint,
            amount=amount_lamports,
            slippage_bps=slippage_bps
        )

        if txid:
            print(f"\nTest Swap Successful! TXID: {txid}")
        else:
            print("\nTest Swap Failed.")

    except Exception as e:
        print(f"\nTest Swap Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main_test())