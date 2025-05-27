# 使用基础镜像
FROM ubuntu:22.04

# 设置工作目录
WORKDIR /app

# 安装Python和pip
RUN apt-get update && \
    apt-get install -y python3.10 python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt ./

# 安装依赖
RUN pip3 install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 启动脚本
CMD ["python3", "script.py"] 