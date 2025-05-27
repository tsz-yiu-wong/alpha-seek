#!/bin/bash

# 设置变量
PROJECT_ID="alpha-seek"
REGION="asia-east1"
IMAGE_NAME="token-price-job"
FULL_IMAGE_NAME="gcr.io/${PROJECT_ID}/${IMAGE_NAME}:latest"

# 输出带颜色的日志
log() {
    echo -e "\033[1;34m[$(date +'%Y-%m-%d %H:%M:%S')] $1\033[0m"
}

error() {
    echo -e "\033[1;31m[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1\033[0m"
    exit 1
}

# 检查是否安装了必要的工具
check_requirements() {
    log "检查必要的工具..."
    command -v docker >/dev/null 2>&1 || error "需要安装 Docker"
    command -v gcloud >/dev/null 2>&1 || error "需要安装 Google Cloud SDK"
}

# 检查 gcloud 是否已登录
check_auth() {
    log "检查 Google Cloud 认证状态..."
    if ! gcloud auth print-access-token >/dev/null 2>&1; then
        log "需要登录 Google Cloud..."
        gcloud auth login
    fi
}

# 构建 Docker 镜像
build_image() {
    log "构建 Docker 镜像..."
    docker buildx build --platform linux/amd64 -t ${IMAGE_NAME} . || error "Docker 构建失败"
}

# 给镜像打标签
tag_image() {
    log "给镜像打标签..."
    docker tag ${IMAGE_NAME} ${FULL_IMAGE_NAME} || error "镜像打标签失败"
}

# 推送镜像到 GCR
push_image() {
    log "推送镜像到 Google Container Registry..."
    docker push ${FULL_IMAGE_NAME} || error "镜像推送失败"
}

# 更新 Cloud Run Job
update_job() {
    log "更新 Cloud Run Job..."
    gcloud run jobs update ${IMAGE_NAME} \
        --image ${FULL_IMAGE_NAME} \
        --region ${REGION} \
        --memory 2Gi \
        --cpu 2 \
        --timeout 900s \
        --max-retries 3 || error "Cloud Run Job 更新失败"
}

# 主函数
main() {
    log "开始部署流程..."
    
    # 检查环境
    check_requirements
    check_auth
    
    # 设置项目
    gcloud config set project ${PROJECT_ID}
    
    # 执行部署步骤
    build_image
    tag_image
    push_image
    update_job
    
    log "部署完成！"
}

# 执行主函数
main 