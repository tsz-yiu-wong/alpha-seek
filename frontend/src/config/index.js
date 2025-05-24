// 检测当前环境
const isDevelopment = process.env.NODE_ENV === 'development';

// 使用环境变量或默认值
const apiBaseUrl = process.env.VUE_APP_API_BASE_URL || 'http://localhost:8080';
const wsBaseUrl = process.env.VUE_APP_WS_BASE_URL || 'ws://localhost:8080';


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

// 确保 WebSocket URL 格式正确
if (config.wsBaseUrl.startsWith('https://')) {
  config.wsBaseUrl = config.wsBaseUrl.replace('https://', 'wss://');
} else if (config.wsBaseUrl.startsWith('http://')) {
  config.wsBaseUrl = config.wsBaseUrl.replace('http://', 'ws://');
}

// 确保URL不以斜杠结尾，避免路径问题
if (config.wsBaseUrl.endsWith('/')) {
  config.wsBaseUrl = config.wsBaseUrl.slice(0, -1);
}

// 在开发环境中输出配置信息
if (isDevelopment) {
  console.log('App config:', config);
}

export default config; 