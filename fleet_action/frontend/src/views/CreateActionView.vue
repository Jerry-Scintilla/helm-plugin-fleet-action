<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api, type Character } from '@/api'
import { t } from '@/i18n'

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
    error.value = t('create.err.load') + (e as Error).message
  }
})

async function submit() {
  if (!form.value.name.trim()) { error.value = t('create.err.noName'); return }
  if (!form.value.fc_character_id) { error.value = t('create.err.noFC'); return }

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
      <span class="page-title">{{ t('create.title') }}</span>
    </div>

    <div class="card" style="max-width:560px">
      <div v-if="error" class="error-msg">{{ error }}</div>

      <div class="form-group">
        <label class="form-label">{{ t('create.field.name') }} <span style="color:var(--error-text)">*</span></label>
        <input class="form-control" v-model="form.name" placeholder="e.g. Brave Newbies Roam" maxlength="256" />
      </div>

      <div class="form-group">
        <label class="form-label">{{ t('create.field.desc') }}</label>
        <textarea class="form-control" v-model="form.description" :placeholder="t('create.desc.placeholder')" maxlength="2048" />
      </div>

      <div class="form-group">
        <label class="form-label">{{ t('create.field.fc') }} <span style="color:var(--error-text)">*</span></label>
        <select class="form-control" v-model="form.fc_character_id">
          <option v-if="characters.length === 0" :value="0" disabled>{{ t('create.chars.loading') }}</option>
          <option v-for="c in characters" :key="c.value" :value="c.value">{{ c.label }}</option>
        </select>
      </div>

      <div class="btn-row" style="margin-top:8px">
        <button class="btn btn-primary" :disabled="submitting" @click="submit">
          {{ submitting ? t('create.submitting') : t('create.submit') }}
        </button>
        <button class="btn" @click="router.back()">{{ t('cancel') }}</button>
      </div>
    </div>
  </div>
</template>
