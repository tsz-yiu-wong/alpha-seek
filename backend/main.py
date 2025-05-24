# main.py
import asyncio
import sys
import os

# 确保可以正确导入 backend 包
# 这会将项目根目录添加到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 从各自的模块导入主循环/启动函数
# 注意：确保 handler 和 runner 中的 main 函数和初始化是兼容的
# 可能需要稍微调整 handler.py 和 runner.py，让它们可以被导入并调用其主函数
# 例如，将它们的主逻辑封装在一个 async main() 函数中，并移除 if __name__ == \"__main__\": asyncio.run(...)
from backend.data.handler import main_data_loop
from backend.runner import main as runner_main # 假设 runner 的主逻辑在 async def main() 中

async def start_services():
    """同时启动数据处理器和策略运行器"""
    print("Starting services...")

    # 创建数据处理循环任务
    # 可以从配置或环境变量读取 time_interval
    data_task = asyncio.create_task(main_data_loop(time_interval=30))
    print("Data handler task created.")

    # 创建策略运行器任务
    runner_task = asyncio.create_task(runner_main())
    print("Runner task created.")

    # 等待两个任务完成（在这个例子中，它们会一直运行直到被中断）
    # 使用 asyncio.gather 来同时运行并等待它们
    # try/except 可以捕获其中一个任务失败的情况
    try:
        await asyncio.gather(data_task, runner_task)
    except Exception as e:
        print(f"An error occurred: {e}")
        # 取消其他任务
        if not data_task.done(): data_task.cancel()
        if not runner_task.done(): runner_task.cancel()
        # 等待任务取消完成
        await asyncio.gather(data_task, runner_task, return_exceptions=True)
        print("Tasks cancelled.")

if __name__ == "__main__":
    try:
        asyncio.run(start_services())
    except KeyboardInterrupt:
        print("\nServices stopped by user.")
    except Exception as e:
        print(f"\nMain application crashed: {e}")
        import traceback
        traceback.print_exc()
