# strategy.py
class Strategy2:
    def on_data(self, data):
        # 根据数据做出决策，产生买卖信号
        print(f"策略收到数据：{data}")
        
        #signal = generate_signal(data)
        #dispatcher.handle_signal(signal)
        #return signal
