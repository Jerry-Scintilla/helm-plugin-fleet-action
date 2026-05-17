<script setup lang="ts">
const props = defineProps<{
  message: string
  visible: boolean
}>()

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="confirm-overlay" @click.self="emit('cancel')">
    <div class="confirm-dialog">
      <p>{{ props.message }}</p>
      <div class="confirm-actions">
        <button class="btn btn-primary" @click="emit('confirm')">确定</button>
        <button class="btn" @click="emit('cancel')">取消</button>
      </div>
    </div>
  </div>
  </Teleport>
</template>

<style scoped>
.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}
.confirm-dialog {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 24px 28px;
  max-width: 360px;
  width: 90%;
  text-align: center;
}
.confirm-dialog p {
  color: var(--text-primary);
  font-size: 14px;
  margin-bottom: 20px;
  line-height: 1.5;
}
.confirm-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}
</style>