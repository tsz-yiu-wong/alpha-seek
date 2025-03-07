<template>
  <div class="container">
    <!-- 修改登录按钮的点击事件 -->
    <div class="login-section">
      <button class="login-btn" @click="handleLoginClick">
        <svg class="login-icon" viewBox="0 0 24 24" width="24" height="24">
          <path v-if="!isLoggedIn" fill="currentColor" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
          <path v-else fill="currentColor" d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/>
        </svg>
        {{ isLoggedIn ? 'Logout' : 'Login' }}
      </button>
    </div>

    <div class="time-section">
      <div class="time-box" style="color: red;">
        <span>Last Update: </span>
        <span>{{ data.timestamp }}</span>
      </div>
    </div>
    <br>

    <!-- 上半部分：搜索和DIY token列表 -->
    <div class="favorite-section">
      
      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th class="sticky-col-1">Tag</th>
              <th class="sticky-col-2">Token</th>
              <th class="sticky-col-3">Chain</th>
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
              <th class="sticky-col-last">Edit</th>
            </tr>
          </thead>
          <tbody>
            <!-- 如果未登录，显示登录提示 -->
            <tr v-if="!isLoggedIn">
              <td colspan="19" class="login-prompt-cell">
                <span>
                  <a href="#" @click.prevent="showLoginDialog = true">Login</a> 
                  to add favorite tokens
                </span>
              </td>
            </tr>
            <!-- 如果已登录，显示token列表 -->
            <tr v-else v-for="token in data.favorite_tokens" :key="token.tokenAddress">
              <td class="sticky-col-1" :class="{ 'inactive-token': token.status === 'inactive' }">
                {{ token.status === 'inactive' ? 'Inactive' : token.tag }}
              </td>
              <td class="sticky-col-2 token-cell" :class="{ 'inactive-token': token.status === 'inactive' }">
                <img :src="token.icon" class="token-icon" />
                <button class="copy-btn" @click="copyUrl(token.tokenAddress)" title="Copy Address">
                  <svg class="copy-icon" viewBox="0 0 24 24" width="14" height="14">
                    <path fill="currentColor" d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>
                  </svg>
                </button>
                <a :href="token.url" target="_blank">{{ token.symbol }}</a>
              </td>
              <td class="sticky-col-3">{{ token.chainId }}</td>
              <td>{{ formatPrice(token.priceNative) }}</td>
              <td>{{ formatPrice(token.priceUsd) }}</td>
              <td :class="getPriceChangeClass(token.priceChange_m5)">
                {{ formatPercentage(token.priceChange_m5) }}
              </td>
              <td :class="getPriceChangeClass(token.priceChange_h1)">
                {{ formatPercentage(token.priceChange_h1) }}
              </td>
              <td :class="getPriceChangeClass(token.priceChange_h6)">
                {{ formatPercentage(token.priceChange_h6) }}
              </td>
              <td :class="getPriceChangeClass(token.priceChange_h24)">
                {{ formatPercentage(token.priceChange_h24) }}
              </td>
              <td> </td>
              <td>{{ formatNumber(token.txns_m5_buy + token.txns_m5_sell) }}</td>
              <td>{{ formatNumber(token.txns_h1_buy + token.txns_h1_sell) }}</td>
              <td>{{ formatNumber(token.txns_h6_buy + token.txns_h6_sell) }}</td>
              <td>{{ formatNumber(token.txns_h24_buy + token.txns_h24_sell) }}</td>
              <td> </td>
              <td>{{ formatUSD(token.volume_m5) }}</td>
              <td>{{ formatUSD(token.volume_h1) }}</td>
              <td>{{ formatUSD(token.volume_h6) }}</td>
              <td>{{ formatUSD(token.volume_h24) }}</td>
              <td class="sticky-col-last">
                <button @click="confirmDelete(token.tokenAddress)" class="delete-btn">
                  -
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 下半部分：Tab切换 -->
    <div class="tabs-section">
      <!-- 恢复 tabs 切换按钮 -->
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

      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th class="sticky-col-1">Tag</th>
              <th class="sticky-col-2">Token</th>
              <th class="sticky-col-3">Chain</th>
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
              <th class="sticky-col-last">Edit</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in currentTabData" :key="item.address">
              <td class="sticky-col-1">{{ item.tag }}</td>
              <td class="sticky-col-2 token-cell">
                <img :src="item.icon" class="token-icon" />
                <button class="copy-btn" @click="copyUrl(item.tokenAddress)" title="Copy Address">
                  <svg class="copy-icon" viewBox="0 0 24 24" width="14" height="14">
                    <path fill="currentColor" d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>
                  </svg>
                </button>
                <a :href="item.url" target="_blank">{{ item.symbol }}</a>
              </td>
              <td class="sticky-col-3">{{ item.chainId }}</td>
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
              <td class="sticky-col-last">
                <button 
                  v-if="isLoggedIn" 
                  @click="addToFavorite({
                    tokenAddress: item.tokenAddress,
                    icon: item.icon,
                    url: item.url,
                    chainId: item.chainId
                  })" 
                  class="add-btn"
                  title="Add to favorites"
                >
                  <span>+</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 登录对话框只在未登录时显示 -->
    <LoginDialog 
      :show="showLoginDialog && !isLoggedIn" 
      @close="showLoginDialog = false"
    />

    <!-- 添加确认对话框 -->
    <ConfirmDialog
      :show="showConfirmDialog"
      message="Are you sure you want to delete this token?"
      @confirm="handleDeleteConfirm"
      @close="showConfirmDialog = false"
    />
  </div>
</template>

<script>
import LoginDialog from '../components/LoginDialog.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import { mapState } from 'vuex'

export default {
  name: 'Home',
  components: {
    LoginDialog,
    ConfirmDialog
  },
  data() {
    return {
      tokenAddress: '',
      // 恢复并修改 tabs 相关配置
      currentTab: 'solana_pool',
      tabs: [
        { key: 'solana_pool', label: 'Solana' },
        { key: 'base_pool', label: 'Base' },
        { key: 'bsc_pool', label: 'BSC' }
      ],
      showLoginDialog: false,
      showConfirmDialog: false,
      tokenToDelete: null
    }
  },
  computed: {
    data() {
      return this.$store.state.data
    },
    currentTabData() {
      const mapping = {
        solana_pool: this.data.solana_pool || [],
        base_pool: this.data.base_pool || [],
        bsc_pool: this.data.bsc_pool || []
      }
      return mapping[this.currentTab] || []
    },
    ...mapState(['data', 'isLoggedIn'])
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
      const num = Number(price)
      return num.toExponential(3)
    },
    formatPercentage(value) {
      if (!value && value !== 0) return '-'
      return `${Number(value).toFixed(2)}%`
    },
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
    copyUrl(url) {
      if (!url) return
      navigator.clipboard.writeText(url)
        .catch(err => {
          console.error('复制失败:', err)
        })
    },
    handleLoginClick() {
      if (this.isLoggedIn) {
        this.$store.dispatch('logout')
      } else {
        this.showLoginDialog = true
      }
    },
    async addToFavorite(tokenData) {
      try {
        await this.$store.dispatch('addToFavorite', tokenData)
      } catch (error) {
        console.error('Failed to add token:', error)
      }
    },
    confirmDelete(tokenAddress) {
      this.tokenToDelete = tokenAddress
      this.showConfirmDialog = true
    },
    async handleDeleteConfirm() {
      if (this.tokenToDelete) {
        try {
          await this.$store.dispatch('deleteFavorite', this.tokenToDelete)
          this.showConfirmDialog = false
          this.tokenToDelete = null
        } catch (error) {
          console.error('Failed to delete token:', error)
        }
      }
    }
  },
  mounted() {
    this.$store.dispatch('initWebSocket')
    // 初始化时请求更新数据
    this.$store.dispatch('requestUpdate')
  }
}
</script>

<style scoped>
.container {
  padding: 20px;
  max-width: 100%;
}

.favorite-section {
  margin-top: 20px;
  margin-bottom: 50px;
}

.table-wrapper {
  overflow-x: auto;
  white-space: nowrap;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  position: relative;
}

.data-table {
  width: 100%;
  min-width: 1800px;
  border-collapse: collapse;
  background: white;
  table-layout: fixed;
}

.data-table th,
.data-table td {
  padding: 10px;
  text-align: left;
  border-bottom: 1px solid #eee;
  box-sizing: border-box;
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
  width: 100%;
  overflow: hidden;
}

/* 调整 token 单元格内元素的顺序 */
.token-cell img.token-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  flex-shrink: 0;
  order: 1; /* 图标放第一位 */
}

.token-cell .copy-btn {
  padding: 2px;
  background: transparent;
  border: none;
  cursor: pointer;
  color: #6c757d;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
  flex-shrink: 0;
  order: 2; /* 复制按钮放第二位 */
}

.token-cell a {
  color: #2c3e50;
  text-decoration: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
  order: 3; /* 名称放第三位 */
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


@media (max-width: 768px) {
  .container {
    padding: 10px;
  }
}

.price-up {
  color: #28a745;
}

.price-down {
  color: #dc3545;
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
  flex-shrink: 0;
}

.copy-btn:hover {
  color: #2c3e50;
  background: #f8f9fa;
}

.copy-icon {
  width: 14px;
  height: 14px;
}

/* 基础固定列样式 */
.data-table th[class*="sticky-col"],
.data-table td[class*="sticky-col"] {
  position: sticky;
  background: white;
  z-index: 2;
}

/* 表头的固定列需要更高的 z-index 和不同的背景色 */
.data-table th[class*="sticky-col"] {
  background: #f8f9fa;
  z-index: 3;
}

/* 各列的位置定义 */
.data-table .sticky-col-1 {
  left: 0;
  width: 50px;
}

.data-table .sticky-col-2 {
  left: 50px;
  width: 160px;
}

.data-table .sticky-col-3 {
  left: 210px;
  width: 70px;
}

.data-table .sticky-col-last {
  right: 0;
  width: 60px;
}

/* 为其他列设置固定宽度 */
.data-table th:nth-child(4),
.data-table td:nth-child(4) {
  padding-left: 10px;
  width: 100px; /* Price 列 */
}

.data-table th:nth-child(5),
.data-table td:nth-child(5) {
  width: 100px; /* PriceUSD 列 */
}

/* 百分比变化列 */
.data-table th:nth-child(6),
.data-table td:nth-child(6),
.data-table th:nth-child(7),
.data-table td:nth-child(7),
.data-table th:nth-child(8),
.data-table td:nth-child(8),
.data-table th:nth-child(9),
.data-table td:nth-child(9) {
  width: 110px;
}

/* Txns 标题列 */
.data-table th:nth-child(10),
.data-table td:nth-child(10) {
  width: 60px;
}

/* Txns 数据列 */
.data-table th:nth-child(11),
.data-table td:nth-child(11),
.data-table th:nth-child(12),
.data-table td:nth-child(12),
.data-table th:nth-child(13),
.data-table td:nth-child(13),
.data-table th:nth-child(14),
.data-table td:nth-child(14) {
  width: 80px;
}

/* Volume 标题列 */
.data-table th:nth-child(15),
.data-table td:nth-child(15) {
  width: 60px;
}

/* Volume 数据列 */
.data-table th:nth-child(16),
.data-table td:nth-child(16),
.data-table th:nth-child(17),
.data-table td:nth-child(17),
.data-table th:nth-child(18),
.data-table td:nth-child(18),
.data-table th:nth-child(19),
.data-table td:nth-child(19) {
  width: 120px;
}

/* 第三列右侧阴影 */
.data-table td.sticky-col-3::after,
.data-table th.sticky-col-3::after {
  content: '';
  position: absolute;
  top: 0;
  right: -5px;
  bottom: 0;
  width: 5px;
  background: linear-gradient(to right, rgba(0,0,0,0.1), transparent);
  pointer-events: none;
}

/* 最后一列左侧阴影 */
.data-table td.sticky-col-last::before,
.data-table th.sticky-col-last::before {
  content: '';
  position: absolute;
  top: 0;
  left: -5px;
  bottom: 0;
  width: 5px;
  background: linear-gradient(to left, rgba(0,0,0,0.1), transparent);
  pointer-events: none;
}

.login-section {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 100;
}

.login-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background: #6c5ce7;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
}

.login-btn:hover {
  background: #5f4dd0;
}

.login-icon {
  width: 20px;
  height: 20px;
}

.login-prompt-cell {
  text-align: center;
  padding: 30px !important;
  background: #f8f9fa;
  border-bottom: 1px solid #eee;
}

/* 添加新的样式来确保内容水平居中 */
.login-prompt-cell span {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  width: 100%;
}

.login-prompt-cell a {
  color: #6c5ce7;
  text-decoration: none;
  font-weight: bold;
}

.login-prompt-cell a:hover {
  text-decoration: underline;
}

.delete-btn {
  padding: 4px 8px;
  background: #ff6b6b;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}

.delete-btn:hover {
  background: #e53935;
}

.add-btn {
  padding: 4px 8px;
  background: #6c5ce7;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}

.add-btn:hover {
  background: #5f4dd0;
}

/* 添加不活跃token的样式 */
.inactive-token {
  opacity: 0.5;
  color: #999;
}

.inactive-token a {
  color: #999;
}
</style>

