import { createStore } from 'vuex'

export default createStore({
  state: {
    ws: null,
    isConnected: false,
    data: {}
  },
  mutations: {
    SET_WEBSOCKET(state, ws) {
      state.ws = ws
    },
    SET_CONNECTION_STATUS(state, status) {
      state.isConnected = status
    },
    UPDATE_DATA(state, data) {
      state.data = data
    }
  },
  actions: {
    initWebSocket({ commit, state }) {
      if (state.ws) return // 如果已经存在连接，就不再创建新的

      const ws = new WebSocket('ws://localhost:8000/ws')
      
      ws.onopen = () => {
        commit('SET_CONNECTION_STATUS', true)
      }
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        commit('UPDATE_DATA', data)
      }
      
      ws.onclose = () => {
        commit('SET_CONNECTION_STATUS', false)
      }
      
      commit('SET_WEBSOCKET', ws)
    },
    closeWebSocket({ state, commit }) {
      if (state.ws) {
        state.ws.close()
        commit('SET_WEBSOCKET', null)
        commit('SET_CONNECTION_STATUS', false)
      }
    }
  }
}) 