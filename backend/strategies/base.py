from abc import ABC, abstractmethod
from collections import namedtuple

# 定义交易信号结构
Signal = namedtuple("Signal", ["action", "token", "amount", "confidence", "pair_address"]) # 添加 pair_address

class BaseStrategy(ABC):
    """策略基类"""
    def __init__(self, token_symbol: str, pair_address: str):
        """
        初始化策略

        :param token_symbol: 策略关注的代币符号 (例如 'WIF', 'BONK')
        :param pair_address: 策略关注的交易对地址 (例如 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v')
        """
        self.token_symbol = token_symbol
        self.pair_address = pair_address
        print(f"Strategy initialized for token: {self.token_symbol} ({self.pair_address})")

    @abstractmethod
    async def on_data(self, data: dict) -> Signal | None:
        """
        处理来自事件总线的数据，并决定是否生成交易信号。

        :param data: 从 handler.py 接收到的标准化代币数据字典。
                      预期包含价格、交易量等信息。
                      例如: {'pairAddress': '...', 'priceUsd': '...', 'volume': {...}, 'baseToken': {'address': '...'}, ...}
        :return: 如果满足交易条件，返回一个 Signal 对象；否则返回 None。
        """
        pass
