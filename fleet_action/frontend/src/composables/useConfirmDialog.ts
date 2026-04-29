import { ref } from 'vue'

const message = ref('')
const _resolve = ref<((value: boolean) => void) | null>(null)

export function useConfirmDialog() {
  function confirm(msg: string): Promise<boolean> {
    message.value = msg
    return new Promise<boolean>((resolve) => {
      _resolve.value = (value: boolean) => {
        _resolve.value = null
        resolve(value)
      }
    })
  }

  return { message, _resolve, confirm }
}