import { createStore } from 'vuex'
import axios from 'axios'
import config from '../config'

export default createStore({
  state: {
    ws: null,
    isConnected: false,
    data: {},
    isLoggedIn: false,
    username: null
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
    },
    SET_LOGIN_STATUS(state, { status, username }) {
      state.isLoggedIn = status
      state.username = username
    }
  },
  actions: {
    initWebSocket({ commit, state }) {
      if (state.ws) return // 如果已经存在连接，就不再创建新的

      const ws = new WebSocket(`${config.wsBaseUrl}/ws`)
      
      ws.onopen = () => {
        commit('SET_CONNECTION_STATUS', true)
        // WebSocket 连接建立后立即请求数据
        ws.send(JSON.stringify({ type: 'request_update' }))
        
        // 如果用户已登录，重新发送登录信息
        if (state.isLoggedIn && state.username) {
          ws.send(JSON.stringify({
            type: 'login',
            username: state.username
          }))
        }
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
    },
    async login({ commit, state }, credentials) {
      try {
        const response = await axios.post(`${config.apiBaseUrl}/api/login`, credentials)
        if (response.data.status === 'success') {
          commit('SET_LOGIN_STATUS', { 
            status: true, 
            username: response.data.username 
          })
          
          // 登录成功后通过 WebSocket 发送用户名
          if (state.ws && state.ws.readyState === WebSocket.OPEN) {
            state.ws.send(JSON.stringify({
              type: 'login',
              username: response.data.username
            }))
          }
          
          return true
        }
      } catch (error) {
        console.error('Login failed:', error)
        return false
      }
    },
    logout({ commit }) {
      commit('SET_LOGIN_STATUS', { status: false, username: null })
    },
    async requestUpdate({ state }) {
      if (state.ws && state.ws.readyState === WebSocket.OPEN) {
        state.ws.send(JSON.stringify({ type: 'request_update' }))
      }
    },
    async addToFavorite({ state, commit }, tokenData) {
      if (!state.isLoggedIn) return false
      
      try {
        const response = await axios.post(`${config.apiBaseUrl}/api/add_favorite`, {
          username: state.username,
          tokenData: tokenData
        })
        if (response.data.status === 'success') {
          // 更新状态
          commit('UPDATE_DATA', response.data.data)
          return true
        }
      } catch (error) {
        console.error('Add favorite failed:', error)
        return false
      }
    },
    async deleteFavorite({ state, commit }, tokenAddress) {
      if (!state.isLoggedIn) return false
      
      try {
        const response = await axios.post(`${config.apiBaseUrl}/api/delete_favorite`, {
          username: state.username,
          tokenAddress: tokenAddress
        })
        if (response.data.status === 'success') {
          // 更新状态
          commit('UPDATE_DATA', response.data.data)
          return true
        }
      } catch (error) {
        console.error('Delete favorite failed:', error)
        return false
      }
    }
  }
}) 