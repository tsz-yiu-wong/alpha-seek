# 策略信号接收、风控判断、执行下单

import time
import traceback
from .solana_trade import perform_swap, SOL_MINT_ADDRESS # 导入执行函数和 SOL mint 地址
from solana.rpc.api import Client
from solders.keypair import Keypair
from .solana_wallet import load_wallet # 导入钱包加载

# Placeholder for the actual trading module implementation or import
# This module should provide the buy/sell methods.
class MockTradingModule:
    async def buy(self, token_mint: str, amount_sol: float, wallet: Keypair, client: Client):
        print(f"[Mock] Executing BUY: Token={token_mint}, Amount={amount_sol} SOL")
        # Simulate successful trade
        await asyncio.sleep(0.1) # Simulate network delay
        return f"mock_txid_buy_{int(time.time())}"

    async def sell(self, token_mint: str, amount_token: float, wallet: Keypair, client: Client):
        print(f"[Mock] Executing SELL: Token={token_mint}, Amount={amount_token} TokenUnits")
        # Simulate successful trade
        await asyncio.sleep(0.1)
        return f"mock_txid_sell_{int(time.time())}"


class SolanaTradingModule:
    """使用 solana_trade.py 执行实际 Solana 交易的模块"""
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.rpc_url = rpc_url
        # 客户端和钱包在执行交易时加载，以确保使用最新的状态
        print(f"SolanaTradingModule initialized with RPC: {self.rpc_url}")

    async def buy(self, token_mint: str, amount_sol: float, wallet_index: int = 0):
        """
        执行买入操作 (SOL -> Token)
        :param token_mint: 要购买的代币的 mint 地址
        :param amount_sol: 用于购买的 SOL 数量
        :param wallet_index: 使用的钱包索引
        :return: 交易 ID 或 None
        """
        print(f"[Solana] Initiating BUY: {amount_sol} SOL -> Token {token_mint} using wallet {wallet_index}")
        try:
            wallet = load_wallet(wallet_index)
            client = Client(self.rpc_url)
            # 注意：Jupiter API 需要 lamports (1 SOL = 1,000,000,000 lamports)
            amount_lamports = int(amount_sol * 1e9)
            txid = await perform_swap(
                wallet=wallet,
                client=client,
                input_mint=SOL_MINT_ADDRESS, # 从 SOL 买入
                output_mint=token_mint,    # 买入目标代币
                amount=amount_lamports,    # 以 lamports 为单位的数量
                slippage_bps=50 # 示例：设置滑点为 0.5%
            )
            return txid
        except Exception as e:
            print(f"[Solana] BUY failed for {token_mint}: {e}")
            traceback.print_exc()
            return None

    async def sell(self, token_mint: str, amount_token: float, wallet_index: int = 0):
        """
        执行卖出操作 (Token -> SOL)
        :param token_mint: 要卖出的代币的 mint 地址
        :param amount_token: 要卖出的代币数量 (以代币的最小单位计，需要策略或调用者确保)
                               # TODO: 确认 Jupiter 是否需要代币的最小单位，如果策略信号中的 amount 是浮点数，需要转换
                               # 假设 amount_token 已经是正确的最小单位数量 (e.g., for USDC with 6 decimals, amount=1 means 0.000001 USDC)
        :param wallet_index: 使用的钱包索引
        :return: 交易 ID 或 None
        """
        print(f"[Solana] Initiating SELL: {amount_token} units of {token_mint} -> SOL using wallet {wallet_index}")
        try:
            wallet = load_wallet(wallet_index)
            client = Client(self.rpc_url)
            # 确保 amount_token 是整数
            amount_units = int(amount_token)
            txid = await perform_swap(
                wallet=wallet,
                client=client,
                input_mint=token_mint,       # 卖出目标代币
                output_mint=SOL_MINT_ADDRESS, # 换成 SOL
                amount=amount_units,       # 以代币最小单位计的数量
                slippage_bps=50
            )
            return txid
        except Exception as e:
            print(f"[Solana] SELL failed for {token_mint}: {e}")
            traceback.print_exc()
            return None


# Rename Dispatcher to TradeExecutor for clarity
class TradeExecutor:
    def __init__(self, trading_module, default_wallet_index: int = 0):
        if trading_module is None:
            print("Warning: No trading module provided to TradeExecutor. Using MockTradingModule.")
            self.trading_module = MockTradingModule() # 保持 Mock 作为备选
        else:
            self.trading_module = trading_module
        self.default_wallet_index = default_wallet_index
        print(f"TradeExecutor initialized with trading module: {type(trading_module).__name__} and default wallet index: {default_wallet_index}")

    async def handle_signal(self, signal):
        """Receives a signal, performs risk checks, and executes the trade asynchronously."""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        # 風控檢查：例如，检查信号的置信度是否足够高
        if not signal:
             print(f"[{timestamp}] Received empty signal. Skipping.")
             return

        # 检查信号类型和必要属性 (从 base.py 导入 Signal)
        # from ..strategies.base import Signal # 避免循环导入，最好在 runner.py 处理信号类型
        # if not isinstance(signal, Signal): # 或者直接检查属性
        required_attrs = ['action', 'token', 'amount', 'confidence', 'pair_address']
        if not all(hasattr(signal, attr) for attr in required_attrs):
             print(f"[{timestamp}] Signal object missing required attributes: {signal}")
             return

        # --- 基本风控 --- #
        if signal.confidence < 0.9: # Example risk check
            print(f"[{timestamp}] Signal confidence ({signal.confidence:.2f}) for {signal.token} below threshold 0.9. Skipping execution.")
            return

        # TODO: 添加更多风控检查
        # - 检查交易金额是否在合理范围内
        # - 检查钱包余额 (虽然 solana_trade.py 里也有检查，但这里可以做初步判断)
        # - 检查是否有正在进行的同一代币的交易
        # - 全局风险，如最大亏损限制等
        print(f"[{timestamp}] Risk checks passed for signal: Action={signal.action}, Token={signal.token}, Amount={signal.amount}, Confidence={signal.confidence:.2f}")

        # --- 执行交易 --- #
        await self.execute_trade(signal)

    async def execute_trade(self, signal):
        """Executes the trade based on the signal using the trading module asynchronously."""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Executing trade for signal: {signal.action} {signal.amount} of {signal.token}")
        txid = None
        try:
            if signal.action == "buy":
                # 假设 signal.amount 是以 SOL 计价的数量
                txid = await self.trading_module.buy(
                    token_mint=signal.token,
                    amount_sol=float(signal.amount),
                    wallet_index=self.default_wallet_index
                )
            elif signal.action == "sell":
                # 假设 signal.amount 是以代币最小单位计价的数量
                # !! 重要: 策略需要提供正确的代币单位数量 !!
                # 如果策略提供的是浮点数量，需要在这里或 SolanaTradingModule 中查询代币精度并转换
                txid = await self.trading_module.sell(
                    token_mint=signal.token,
                    amount_token=int(signal.amount), # 确保是整数
                    wallet_index=self.default_wallet_index
                )
            else:
                print(f"[{timestamp}] Unknown signal action: {signal.action}")

            if txid:
                print(f"[{timestamp}] Trade successful for {signal.token}. Transaction ID: {txid}")
            else:
                print(f"[{timestamp}] Trade failed or was not executed for {signal.token}.")

        except Exception as e:
            print(f"[{timestamp}] Error executing trade for signal {signal}: {e}")
            traceback.print_exc()
            # Add more robust error handling/logging

# 需要导入 asyncio 以运行 Mock 模块中的 async sleep
import asyncio
