// 检测当前环境
const isDevelopment = process.env.NODE_ENV === 'development';

// 使用环境变量或默认值
const apiBaseUrl = process.env.VUE_APP_API_BASE_URL || 'http://backend:8000';
const wsBaseUrl = process.env.VUE_APP_WS_BASE_URL || 'ws://backend:8000';

// 基础配置
const config = {
  apiBaseUrl,
  wsBaseUrl,
  
  // 其他全局配置
  appName: 'alphaseek',
  defaultPageSize: 20,
  
  // 超时设置
  timeouts: {
    apiRequest: 30000, // 30秒
    websocket: 60000   // 60秒
  },
  
  // 功能开关
  features: {
    enableNotifications: true,
    enableDarkMode: false
  }
};

// 计算派生值
// config.wsBaseUrl = config.apiBaseUrl.replace(/^http/, 'ws');

// 在开发环境中输出配置信息
if (isDevelopment) {
  console.log('App config:', config);
}

export default config; 