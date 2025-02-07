<template>
  <div class="container">
    <h1>Meme Coin 实时数据</h1>
    
    <div class="data-section">
      <h2>Token Profiles</h2>
      <div class="data-card">
        <pre>{{ formatJson(data.profiles) }}</pre>
      </div>
    </div>

    <div class="data-section">
      <h2>Latest Token Boosts</h2>
      <div class="data-card">
        <pre>{{ formatJson(data.latest_boosts) }}</pre>
      </div>
    </div>

    <div class="data-section">
      <h2>Top Token Boosts</h2>
      <div class="data-card">
        <pre>{{ formatJson(data.top_boosts) }}</pre>
      </div>
    </div>

    <div class="data-section">
      <h2>Token Pairs</h2>
      <div class="data-card">
        <pre>{{ formatJson(data.pairs) }}</pre>
      </div>
    </div>

    <div class="status-bar">
      <span>最后更新: {{ data.timestamp || '等待数据...' }}</span>
      <span :class="['connection-status', { 'connected': isConnected }]">
        {{ isConnected ? '已连接' : '未连接' }}
      </span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Home',
  data() {
    return {
      data: {
        profiles: null,
        latest_boosts: null,
        top_boosts: null,
        pairs: null,
        timestamp: null
      },
      ws: null,
      isConnected: false
    }
  },
  mounted() {
    this.connectWebSocket()
  },
  beforeUnmount() {
    this.disconnectWebSocket()
  },
  methods: {
    connectWebSocket() {
      this.ws = new WebSocket('ws://localhost:8000/ws')
      
      this.ws.onopen = () => {
        this.isConnected = true
        console.log('WebSocket connected')
      }
      
      this.ws.onmessage = (event) => {
        const newData = JSON.parse(event.data)
        this.data = { ...this.data, ...newData }
      }
      
      this.ws.onclose = () => {
        this.isConnected = false
        console.log('WebSocket disconnected')
        // 尝试重新连接
        setTimeout(() => {
          this.connectWebSocket()
        }, 3000)
      }
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.isConnected = false
      }
    },
    disconnectWebSocket() {
      if (this.ws) {
        this.ws.close()
        this.ws = null
      }
    },
    formatJson(data) {
      if (!data) return '等待数据...'
      return JSON.stringify(data, null, 2)
    }
  }
}
</script>

<style scoped>
.container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.data-section {
  margin-bottom: 30px;
}

.data-section h2 {
  color: #2c3e50;
  margin-bottom: 10px;
}

.data-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: monospace;
  font-size: 14px;
}

.status-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #fff;
  padding: 10px 20px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.connection-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 14px;
  background: #dc3545;
  color: white;
}

.connection-status.connected {
  background: #28a745;
}

@media (max-width: 768px) {
  .container {
    padding: 10px;
  }
  
  .data-card {
    padding: 10px;
  }
  
  pre {
    font-size: 12px;
  }
}
</style>
