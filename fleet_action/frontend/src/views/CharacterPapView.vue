<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { api, type PapStatsItem } from '@/api'

const props = defineProps<{
  characterId?: number
}>()

const stats = ref<{
  character_id: number
  total_count: number
  this_month_count: number
  this_year_count: number
  records: PapStatsItem[]
} | null>(null)

const loading = ref(false)
const error = ref('')

const effectiveCharacterId = computed(() => {
  const urlParams = new URLSearchParams(window.location.search)
  const queryId = urlParams.get('character_id')
  return props.characterId || (queryId ? parseInt(queryId) : null)
})

async function load() {
  if (!effectiveCharacterId.value) {
    error.value = '缺少 character_id 参数'
    return
  }
  loading.value = true
  error.value = ''
  try {
    stats.value = await api.getCharacterPapStats(effectiveCharacterId.value)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

function formatDate(dt: string | Date | null) {
  if (!dt) return '—'
  return new Date(dt).toLocaleString('zh-CN', { hour12: false })
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <span class="page-title">PAP 出勤记录</span>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>

    <!-- Stats summary -->
    <div class="stats-grid" v-if="stats">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_count }}</div>
        <div class="stat-label">总出勤次数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.this_month_count }}</div>
        <div class="stat-label">本月出勤</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.this_year_count }}</div>
        <div class="stat-label">本年出勤</div>
      </div>
    </div>

    <!-- Records timeline -->
    <div class="card" style="padding:0; margin-top:20px; overflow:hidden" v-if="stats">
      <table class="data-table">
        <thead>
          <tr>
            <th>行动名称</th>
            <th>指挥官</th>
            <th>出勤日期</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="3" class="empty-msg">加载中…</td>
          </tr>
          <tr v-else-if="stats.records.length === 0">
            <td colspan="3" class="empty-msg">暂无出勤记录</td>
          </tr>
          <tr v-for="record in stats.records" :key="record.action_id + '-' + record.action_date">
            <td class="text-bright">{{ record.action_name }}</td>
            <td>{{ record.fc_character_name }}</td>
            <td class="text-muted">{{ formatDate(record.action_date) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 16px;
}

.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 24px;
  text-align: center;
}

.stat-value {
  font-family: var(--font-serif);
  font-size: 1.6rem;
  font-weight: 500;
  color: var(--brand);
}

.stat-label {
  font-size: 0.88rem;
  color: var(--text-muted);
  margin-top: 6px;
}
</style>