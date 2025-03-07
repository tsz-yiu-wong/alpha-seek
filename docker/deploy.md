# 部署指南

## 本地开发

1. 确保已安装 Docker 和 Docker Compose
2. 在项目根目录运行：
   ```
   docker-compose -f docker/docker-compose.yml up
   ```
3. 访问：
   - 前端：http://localhost:8080
   - 后端：http://localhost:8000

## 部署到 Google Cloud Run

1. 安装并配置 Google Cloud SDK
2. 启用必要的 API：
   ```
   gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com
   ```
3. 执行构建和部署：
   ```
   gcloud builds submit --config=cloudbuild.yaml
   ```
4. 部署完成后，可以在 Google Cloud Console 中查看服务 URL

## 配置自定义域名

1. 在 Google Cloud Console 中，进入 Cloud Run 服务
2. 选择服务，点击"管理自定义域"
3. 按照向导添加您的域名
4. 更新您的 DNS 记录，指向 Google 提供的 IP 地址 