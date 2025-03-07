<template>
  <div v-if="show" class="confirm-overlay">
    <div class="confirm-dialog">
      <p>{{ message }}</p>
      <div class="buttons">
        <button @click="$emit('confirm')" class="confirm-btn">Yes</button>
        <button @click="$emit('close')" class="cancel-btn">No</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ConfirmDialog',
  props: {
    show: Boolean,
    message: String
  }
}
</script>

<style scoped>
.confirm-overlay {
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

.confirm-dialog {
  background: white;
  padding: 20px;
  border-radius: 8px;
  width: 300px;
  text-align: center;
}

.buttons {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 20px;
}

button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.confirm-btn {
  background: #ff6b6b;
  color: white;
}

.confirm-btn:hover {
  background: #e53935;
}

.cancel-btn {
  background: #e0e0e0;
}

.cancel-btn:hover {
  background: #d5d5d5;
}
</style> 