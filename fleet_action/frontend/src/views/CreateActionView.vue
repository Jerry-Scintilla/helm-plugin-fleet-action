<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api, type Character } from '@/api'

const router = useRouter()

const characters = ref<Character[]>([])
const form = ref({ name: '', description: '', fc_character_id: 0 })
const submitting = ref(false)
const error = ref('')

onMounted(async () => {
  try {
    characters.value = await api.getCharacters()
    if (characters.value.length > 0) {
      form.value.fc_character_id = characters.value[0].value
    }
  } catch (e) {
    error.value = '无法加载角色列表：' + (e as Error).message
  }
})

async function submit() {
  if (!form.value.name.trim()) { error.value = '请填写行动名称'; return }
  if (!form.value.fc_character_id) { error.value = '请选择 FC 角色'; return }

  submitting.value = true
  error.value = ''
  try {
    await api.createAction({
      name: form.value.name.trim(),
      description: form.value.description.trim(),
      fc_character_id: form.value.fc_character_id,
    })
    router.push('/actions')
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <span class="page-title">新建舰队行动</span>
    </div>

    <div class="card" style="max-width:560px">
      <div v-if="error" class="error-msg">{{ error }}</div>

      <div class="form-group">
        <label class="form-label">行动名称 <span style="color:#e07070">*</span></label>
        <input class="form-control" v-model="form.name" placeholder="如：Brave Newbies Roam" maxlength="256" />
      </div>

      <div class="form-group">
        <label class="form-label">行动描述</label>
        <textarea class="form-control" v-model="form.description" placeholder="可选描述" maxlength="2048" />
      </div>

      <div class="form-group">
        <label class="form-label">FC 角色 <span style="color:#e07070">*</span></label>
        <select class="form-control" v-model="form.fc_character_id">
          <option v-if="characters.length === 0" :value="0" disabled>（加载中…）</option>
          <option v-for="c in characters" :key="c.value" :value="c.value">{{ c.label }}</option>
        </select>
      </div>

      <div class="btn-row" style="margin-top:8px">
        <button class="btn btn-primary" :disabled="submitting" @click="submit">
          {{ submitting ? '创建中…' : '创建行动' }}
        </button>
        <button class="btn" @click="router.back()">取消</button>
      </div>
    </div>
  </div>
</template>
