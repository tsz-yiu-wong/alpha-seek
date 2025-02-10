<template>
  <div class="container">

    <div class="time-section">
      <div class="time-box" style="color: red;">
        <span>更新时间：</span>
        <span>{{ data.timestamp }}</span>
      </div>
    </div>
    <br>

    <!-- 上半部分：搜索和DIY token列表 -->
    <div class="search-section">
      <div class="search-box">
        <input 
          type="text" 
          v-model="tokenAddress" 
          placeholder="输入Token地址"
          class="token-input"
        />
        <button @click="addToken" class="add-btn">
          <span>+</span>
        </button>
      </div>
      
      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Tag</th>
              <th>Token</th>
              <th>Price</th>
              <th>PriceUSD</th>
              <th>5m</th>
              <th>1h</th>
              <th>6h</th>
              <th>24h</th>
              <th>Txns</th>
              <th>5m</th>
              <th>1h</th>
              <th>6h</th>
              <th>24h</th>
              <th>Volume</th>
              <th>5m</th>
              <th>1h</th>
              <th>6h</th>
              <th>24h</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="token in data.diy_token" :key="token.address">
              <td class="token-cell">
                <img :src="token.icon" class="token-icon" />
                <a :href="token.url" target="_blank">{{ token.symbol }}</a>
                <button class="copy-btn" @click="copyAddress(token.address)" title="复制地址">
                  <svg class="copy-icon" viewBox="0 0 24 24" width="14" height="14">
                    <path fill="currentColor" d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>
                  </svg>
                </button>
              </td>
              <td>{{ token.age }}</td>
              <td>{{ formatPrice(token.pricenative) }}</td>
              <td>{{ token.price_change_5m }}%</td>
              <td>{{ token.price_change_1h }}%</td>
              <td>{{ token.price_change_6h }}%</td>
              <td>{{ token.price_change_24h }}%</td>
              <td>{{ token.txns_total }}</td>
              <td>{{ token.txns_m5_buy }}</td>
              <td>{{ token.txns_h1_buy }}</td>
              <td>{{ token.txns_h6_buy }}</td>
              <td>{{ token.txns_h24_buy }}</td>
              <td>{{ formatUSD(token.volume_total) }}</td>
              <td>{{ formatUSD(token.volume_m5) }}</td>
              <td>{{ formatUSD(token.volume_h1) }}</td>
              <td>{{ formatUSD(token.volume_h6) }}</td>
              <td>{{ formatUSD(token.volume_h24) }}</td>
              <td>{{ token.tag }}</td>
              <td>
                <button @click="deleteToken(token.address)" class="delete-btn">
                  删除
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 下半部分：Tab切换 -->
    <div class="tabs-section">
      <!-- 暂时隐藏 tabs 切换按钮
      <div class="tabs">
        <button 
          v-for="tab in tabs" 
          :key="tab.key"
          :class="['tab-btn', { active: currentTab === tab.key }]"
          @click="currentTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>
      -->

      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Tag</th>
              <th>Token</th>
              <th>Price</th>
              <th>PriceUSD</th>
              <th>5m</th>
              <th>1h</th>
              <th>6h</th>
              <th>24h</th>
              <th>Txns</th>
              <th>5m</th>
              <th>1h</th>
              <th>6h</th>
              <th>24h</th>
              <th>Volume</th>
              <th>5m</th>
              <th>1h</th>
              <th>6h</th>
              <th>24h</th>
            </tr>
          </thead>
          <tbody>
            <!--<tr v-for="item in currentTabData" :key="item.address">-->
            <tr v-for="item in data.solana_pool" :key="item.address">
              <td>-</td>
              <td class="token-cell">
                <img :src="item.icon" class="token-icon" />
                <a :href="item.url" target="_blank">{{ item.symbol }}</a>
                <button class="copy-btn" @click="copyAddress(item.tokenAddress)" title="Copy Address">
                  <svg class="copy-icon" viewBox="0 0 24 24" width="14" height="14">
                    <path fill="currentColor" d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>
                  </svg>
                </button>
              </td>
              <td>{{ formatPrice(item.priceNative) }}</td>
              <td>{{ formatPrice(item.priceUsd) }}</td>
              <td :class="getPriceChangeClass(item.priceChange_m5)">
                {{ formatPercentage(item.priceChange_m5) }}
              </td>
              <td :class="getPriceChangeClass(item.priceChange_h1)">
                {{ formatPercentage(item.priceChange_h1) }}
              </td>
              <td :class="getPriceChangeClass(item.priceChange_h6)">
                {{ formatPercentage(item.priceChange_h6) }}
              </td>
              <td :class="getPriceChangeClass(item.priceChange_h24)">
                {{ formatPercentage(item.priceChange_h24) }}
              </td>
              <td> </td>
              <td>{{ formatNumber(item.txns_m5_buy + item.txns_m5_sell) }}</td>
              <td>{{ formatNumber(item.txns_h1_buy + item.txns_h1_sell) }}</td>
              <td>{{ formatNumber(item.txns_h6_buy + item.txns_h6_sell) }}</td>
              <td>{{ formatNumber(item.txns_h24_buy + item.txns_h24_sell) }}</td>
              <td> </td>
              <td>{{ formatUSD(item.volume_m5) }}</td>
              <td>{{ formatUSD(item.volume_h1) }}</td>
              <td>{{ formatUSD(item.volume_h6) }}</td>
              <td>{{ formatUSD(item.volume_h24) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Home',
  data() {
    return {
      tokenAddress: '',
      // 注释掉 tabs 相关配置
      /*
      currentTab: 'summary',
      tabs: [
        { key: 'solana_pool', label: 'Summary' },
        { key: 'latest_token', label: 'Latest Token' },
        { key: 'latest_boosts', label: 'Latest Boosts' },
        { key: 'top_boosts', label: 'Top Boosts' }
      ]
      */
    }
  },
  computed: {
    data() {
      return this.$store.state.data
    },
    /*
    currentTabData() {
      const mapping = {
        summary: this.data.solana_pool,
        latest_token: this.data.latest_token,
        latest_boosts: this.data.latest_boosts,
        top_boosts: this.data.top_boosts
      }
      return mapping[this.currentTab] || []
    }
    */
  },
  methods: {
    addToken() {
      if (this.tokenAddress) {
        this.$store.dispatch('addToken', this.tokenAddress)
        this.tokenAddress = ''
      }
    },
    deleteToken(address) {
      this.$store.dispatch('deleteToken', address)
    },

    formatPrice(price) {
      if (!price && price !== 0) return '-'
      console.log('Formatting price:', price, typeof price)
      const num = Number(price)
      return num.toExponential(3)
    },
    formatPercentage(value) {
      if (!value && value !== 0){
        console.log('percentage is null/undefined')
        return '-'
      }
      console.log('Formatting percentage:', value, typeof value)
      return `${Number(value).toFixed(2)}%`    },
    getPriceChangeClass(value) {
      if (!value) return ''
      return value > 0 ? 'price-up' : value < 0 ? 'price-down' : ''
    },
    formatNumber(value) {
      if (!value && value !== 0) return '-'
      const num = Number(value)
      return num.toLocaleString('en-US')
    },
    formatUSD(amount) {
      if (!amount && amount !== 0) return '-'
      const num = Number(amount)
      return `$${num.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 8
      })}`
    },
    copyAddress(address) {
      if (!address) return
      navigator.clipboard.writeText(address)
        .then(() => {
          // 可以添加一个提示，告诉用户复制成功
          alert('地址已复制到剪贴板')
        })
        .catch(err => {
          console.error('复制失败:', err)
        })
    }
  },
  mounted() {
    this.$store.dispatch('initWebSocket')
  }
}
</script>

<style scoped>
.container {
  padding: 20px;
  max-width: 100%;
}

.search-section {
  margin-bottom: 40px;
}

.search-box {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.token-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.add-btn {
  padding: 8px 16px;
  background: #6c5ce7;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.table-wrapper {
  overflow-x: auto;
  white-space: nowrap;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

.data-table th,
.data-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.data-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #2c3e50;
}

.token-cell {
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}

.token-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
}

.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.tab-btn {
  padding: 8px 16px;
  border: none;
  background: #f8f9fa;
  border-radius: 4px;
  cursor: pointer;
}

.tab-btn.active {
  background: #6c5ce7;
  color: white;
}

.delete-btn {
  padding: 4px 8px;
  background: #ff6b6b;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

@media (max-width: 768px) {
  .container {
    padding: 10px;
  }
  
  .search-box {
    flex-direction: column;
  }
}

.price-up {
  color: #28a745;
}

.price-down {
  color: #dc3545;
}

.token-cell a {
  color: #2c3e50;
  text-decoration: none;
  margin-right: 0;
}

.token-cell a:hover {
  text-decoration: underline;
}

.copy-btn {
  padding: 2px;
  background: transparent;
  border: none;
  cursor: pointer;
  color: #6c757d;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: 0;
  border-radius: 4px;
  transition: all 0.2s;
}

.copy-btn:hover {
  color: #2c3e50;
  background: #f8f9fa;
}

.copy-icon {
  width: 14px;
  height: 14px;
}
</style>

