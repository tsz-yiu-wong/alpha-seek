<template>
  <div class="chart-container">
    <div class="chart-header">
      <h2>实时价格走势</h2>
      <select v-model="selectedCoin">
        <option value="doge">Dogecoin</option>
        <option value="shib">Shiba Inu</option>
      </select>
    </div>
    <div ref="chartRef" class="chart"></div>
  </div>
</template>

<script>
export default {
  name: 'RealTimeChart',
  data() {
    return {
      chart: null,
      selectedCoin: 'doge',
      ws: null,
      data: []
    }
  },
  mounted() {
    this.initChart()
    this.connectWebSocket()
  },
  methods: {
    initChart() {
      this.chart = this.$echarts.init(this.$refs.chartRef)
      this.updateChart()
    },
    updateChart() {
      const option = {
        title: {
          text: '币价实时走势'
        },
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'time',
          splitLine: {
            show: false
          }
        },
        yAxis: {
          type: 'value',
          splitLine: {
            show: true
          }
        },
        series: [{
          name: '价格',
          type: 'line',
          data: this.data,
          smooth: true
        }]
      }
      this.chart && this.chart.setOption(option)
    },
    connectWebSocket() {
      this.ws = new WebSocket('ws://localhost:8000/ws')
      this.ws.onmessage = (event) => {
        const newData = JSON.parse(event.data)
        this.data.push([new Date().getTime(), newData.price])
        if (this.data.length > 100) {
          this.data.shift()
        }
        this.updateChart()
      }
    }
  },
  beforeUnmount() {
    if (this.ws) {
      this.ws.close()
    }
    if (this.chart) {
      this.chart.dispose()
    }
  }
}
</script>

<style scoped>
.chart-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.chart {
  height: 400px;
  border: 1px solid #eee;
  border-radius: 4px;
}

select {
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid #ddd;
}
</style> 