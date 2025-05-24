from .base import BaseStrategy, Signal
import time # For logging

class StrategyA(BaseStrategy):
    """策略A：一个有状态的示例策略，跟踪持仓"""

    # --- 策略参数 ---
    BUY_PRICE_THRESHOLD = 0.5    # 示例：价格低于此阈值时考虑买入
    SELL_PRICE_THRESHOLD_GAIN = 0.6 # 示例：价格高于此阈值时考虑止盈卖出
    BUY_AMOUNT_SOL = 0.001       # 示例：每次买入 0.001 SOL 的等值代币
    CONFIDENCE = 0.95            # 交易信号的置信度

    def __init__(self, token_symbol: str, pair_address: str):
        """
        初始化 StrategyA
        :param token_symbol: 代币符号
        :param pair_address: 交易对地址
        """
        super().__init__(token_symbol, pair_address)
        # self.position 结构: {token_mint: {"entry_price": float, "buy_signal_data": dict, "timestamp": float}}
        self.position: dict[str, dict] = {}
        print(f"Strategy A ({self.token_symbol}) initialized with state tracking.")

    async def on_data(self, data: dict) -> Signal | None:
        """
        处理传入的数据，根据持仓状态决定买入或卖出。

        :param data: 标准化后的代币数据字典。
        :return: Signal 对象或 None。
        """
        timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S')
        current_time = time.time()

        try:
            price_usd_str = data.get('priceUsd')
            # 使用 baseToken.address 作为持仓的 key
            token_mint = data.get('baseToken', {}).get('address')

            if not price_usd_str or not token_mint:
                # print(f"[{timestamp_str}] Strategy {self.token_symbol}: Missing priceUsd or baseToken address in data.")
                return None

            price_usd = float(price_usd_str)
            # print(f"[{timestamp_str}] Strategy {self.token_symbol}: Received price {price_usd} for {token_mint}") # Debug

            # --- 检查持仓状态 ---
            if token_mint not in self.position:
                # --- 无持仓：考虑买入 ---
                if self.should_buy(token_mint, price_usd, data):
                    print(f"[{timestamp_str}] Strategy {self.token_symbol}: BUY condition met for {token_mint} at {price_usd:.6f} USD.")
                    return self._create_buy_signal(token_mint, price_usd, data)
            else:
                # --- 有持仓：考虑卖出 ---
                position_info = self.position[token_mint]
                if self.should_sell(token_mint, price_usd, position_info, data):
                    entry_price = position_info.get("entry_price", "N/A")
                    print(f"[{timestamp_str}] Strategy {self.token_symbol}: SELL condition met for {token_mint}. Entry: {entry_price}, Current: {price_usd:.6f} USD.")
                    return self._create_sell_signal(token_mint, price_usd, position_info, data)

        except Exception as e:
            print(f"[{timestamp_str}] Strategy {self.token_symbol}: Error processing data: {e}")
            import traceback
            traceback.print_exc() # 更详细的错误

        return None # 没有生成信号

    def should_buy(self, token_mint: str, current_price: float, data: dict) -> bool:
        """
        判断是否满足买入条件。
        示例：价格低于阈值。
        :param token_mint: 代币 mint 地址
        :param current_price: 当前价格 (USD)
        :param data: 完整的价格数据字典 (可能包含交易量等其他信息)
        :return: True 如果应该买入, False 否则
        """
        # TODO: 实现更复杂的买入逻辑，例如结合交易量、指标等
        return current_price < self.BUY_PRICE_THRESHOLD

    def should_sell(self, token_mint: str, current_price: float, position_info: dict, data: dict) -> bool:
        """
        判断是否满足卖出条件。
        示例：价格高于某个盈利阈值。
        :param token_mint: 代币 mint 地址
        :param current_price: 当前价格 (USD)
        :param position_info: 当前持仓信息 (包含 entry_price 等)
        :param data: 完整的价格数据字典
        :return: True 如果应该卖出, False 否则
        """
        # TODO: 实现更复杂的卖出逻辑，例如止损、时间限制、指标信号等
        entry_price = position_info.get("entry_price")
        if entry_price is None:
            return False # 如果没有入场价信息，则不卖出

        # 示例：简单的止盈逻辑
        if current_price > self.SELL_PRICE_THRESHOLD_GAIN:
             print(f"[Debug] Sell Check: {current_price} > {self.SELL_PRICE_THRESHOLD_GAIN}")
             return True

        # 示例：简单的止损逻辑 (例如比入场价下跌 10%)
        # stop_loss_price = entry_price * 0.9
        # if current_price < stop_loss_price:
        #     print(f"[Debug] Stop Loss triggered: {current_price} < {stop_loss_price}")
        #     return True

        return False

    def _create_buy_signal(self, token_mint: str, current_price: float, data: dict) -> Signal:
        """
        创建买入信号并更新持仓状态。
        """
        signal = Signal(
            action='buy',
            token=token_mint,             # 买入目标代币的 mint 地址
            amount=self.BUY_AMOUNT_SOL,   # 使用 SOL 的数量来买入
            confidence=self.CONFIDENCE,
            pair_address=self.pair_address # 传递 pair_address
        )
        # 更新持仓记录
        self.position[token_mint] = {
            "entry_price": current_price,
            "buy_signal_data": data, # 可以保存触发买入时的完整数据
            "timestamp": time.time()
        }
        print(f"[State Update] Position opened for {token_mint} at {current_price:.6f} USD.")
        return signal

    def _create_sell_signal(self, token_mint: str, current_price: float, position_info: dict, data: dict) -> Signal:
        """
        创建卖出信号并更新持仓状态 (平仓)。
        """
        # TODO: 确定卖出数量。这里假设卖出全部持仓。
        # 实际应用中，需要知道买入时获得了多少代币，或者卖出固定价值的代币。
        # 暂时假设我们卖出与买入等值的 SOL (这不准确，仅作示例)
        # 正确的做法是：在买入确认后记录获得的代币数量，然后在卖出时使用该数量。
        # 或者，卖出信号只指定代币和动作，由 trader 决定卖出数量（比如全部卖出）。
        # 这里我们先简化，让 amount 字段在卖出时可能意义不大，或者需要 trader 特殊处理。
        amount_to_sell = position_info.get("buy_amount_tokens", "ALL") # 假设默认卖出全部

        signal = Signal(
            action='sell',
            token=token_mint,           # 卖出持仓代币的 mint 地址
            amount=amount_to_sell,      # TODO: 决定卖出数量! 可能是代币数量或'ALL'
            confidence=self.CONFIDENCE,
            pair_address=self.pair_address
        )
        # 更新持仓记录 (移除)
        del self.position[token_mint]
        print(f"[State Update] Position closed for {token_mint} at {current_price:.6f} USD.")
        return signal
