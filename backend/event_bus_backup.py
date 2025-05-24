import collections

class EventBus:
    def __init__(self):
        # 使用 defaultdict 可以简化订阅时检查频道是否存在的过程
        self.subscribers = collections.defaultdict(list)

    def subscribe(self, channel: str, callback):
        """订阅指定频道的消息"""
        if callback not in self.subscribers[channel]:
            self.subscribers[channel].append(callback)
            print(f"Callback {callback.__name__} subscribed to channel '{channel}'") # 添加日志
        else:
            print(f"Callback {callback.__name__} already subscribed to channel '{channel}'") # 添加日志


    def unsubscribe(self, channel: str, callback):
        """取消订阅指定频道的消息"""
        if channel in self.subscribers and callback in self.subscribers[channel]:
            self.subscribers[channel].remove(callback)
            print(f"Callback {callback.__name__} unsubscribed from channel '{channel}'") # 添加日志
            # 如果频道没有订阅者了，可以考虑删除该频道键
            if not self.subscribers[channel]:
                del self.subscribers[channel]
                print(f"Channel '{channel}' removed as it has no subscribers.") # 添加日志
        else:
            print(f"Callback {callback.__name__} not found in channel '{channel}' or channel does not exist.") # 添加日志


    def publish(self, channel: str, data):
        """向指定频道发布消息"""
        if channel in self.subscribers:
            print(f"Publishing data to channel '{channel}' for {len(self.subscribers[channel])} subscribers.") # 添加日志
            for callback in self.subscribers[channel]:
                try: # 增加错误处理
                    callback(data)  # 调用策略的回调方法
                except Exception as e:
                    print(f"Error calling callback {callback.__name__} in channel '{channel}': {e}") # 添加错误日志
        else:
            print(f"No subscribers for channel '{channel}'.") # 添加日志
