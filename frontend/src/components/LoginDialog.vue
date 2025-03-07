<template>
  <div v-if="show" class="login-overlay">
    <div class="login-dialog">
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>Username:</label>
          <input type="text" v-model="username" required />
        </div>
        <div class="form-group">
          <label>Password:</label>
          <input type="password" v-model="password" required />
        </div>
        <div class="error" v-if="error">{{ error }}</div>
        <div class="buttons">
          <button type="submit">Login</button>
          <button type="button" @click="$emit('close')">Cancel</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LoginDialog',
  props: {
    show: Boolean
  },
  data() {
    return {
      username: '',
      password: '',
      error: ''
    }
  },
  methods: {
    async handleLogin() {
      const success = await this.$store.dispatch('login', {
        username: this.username,
        password: this.password
      })
      
      if (success) {
        this.$emit('close')
      } else {
        this.error = 'Invalid username or password'
      }
    }
  }
}
</script>

<style scoped>
.login-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.login-dialog {
  background: white;
  padding: 20px;
  border-radius: 8px;
  width: 300px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
}

.form-group input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.buttons {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.error {
  color: red;
  margin-bottom: 10px;
}

button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button[type="submit"] {
  background: #6c5ce7;
  color: white;
}

button[type="button"] {
  background: #e0e0e0;
}
</style> 