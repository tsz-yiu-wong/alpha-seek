import { createStore } from 'vuex'

export default createStore({
  state: {
    coinData: {}
  },
  mutations: {
    updateCoinData(state, data) {
      state.coinData = data
    }
  },
  actions: {
    async fetchCoinData({ commit }, coinId) {
      try {
        const response = await fetch(`http://localhost:8000/api/coins/${coinId}`)
        const data = await response.json()
        commit('updateCoinData', data)
      } catch (error) {
        console.error('Error fetching coin data:', error)
      }
    }
  }
}) 