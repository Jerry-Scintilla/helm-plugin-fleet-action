<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api, type ActionItem } from '@/api'
import { t, dateLocale } from '@/i18n'

const router = useRouter()

const items = ref<ActionItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20

const filterStatus = ref('')
const filterFc = ref('')
const loading = ref(false)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const params: Record<string, string> = {
      page: String(page.value),
      page_size: String(pageSize),
    }
    if (filterStatus.value) params.status = filterStatus.value
    if (filterFc.value) params.fc_character_name = filterFc.value
    const data = await api.listActions(params)
    items.value = data.items
    total.value = data.total
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

function applyFilter() {
  page.value = 1
  load()
}

function resetFilter() {
  filterStatus.value = ''
  filterFc.value = ''
  page.value = 1
  load()
}

const totalPages = () => Math.max(1, Math.ceil(total.value / pageSize))

function goPage(n: number) {
  page.value = n
  load()
}

function formatDate(dt: string | null) {
  if (!dt) return '—'
  return new Date(dt).toLocaleString(dateLocale(), { hour12: false })
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <span class="page-title">{{ t('list.title') }}</span>
      <button class="btn btn-primary" @click="router.push('/actions/create')">{{ t('list.new') }}</button>
    </div>

    <!-- Filter bar -->
    <div class="filter-bar">
      <div class="form-group">
        <label class="form-label">{{ t('list.filter.status') }}</label>
        <select class="form-control" v-model="filterStatus" style="width:120px">
          <option value="">{{ t('all') }}</option>
          <option value="active">{{ t('active') }}</option>
          <option value="ended">{{ t('ended') }}</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">{{ t('list.filter.fc') }}</label>
        <input class="form-control" v-model="filterFc" :placeholder="t('list.filter.placeholder')" style="width:160px"
          @keyup.enter="applyFilter" />
      </div>
      <button class="btn btn-primary" @click="applyFilter" :disabled="loading">{{ t('search') }}</button>
      <button class="btn" @click="resetFilter" :disabled="loading">{{ t('reset') }}</button>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>

    <div class="card" style="padding:0; overflow:hidden">
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>{{ t('list.col.name') }}</th>
            <th>{{ t('list.col.fc') }}</th>
            <th>{{ t('list.col.pap') }}</th>
            <th>{{ t('list.col.status') }}</th>
            <th>{{ t('list.col.created') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="6" class="empty-msg">{{ t('loading') }}</td>
          </tr>
          <tr v-else-if="items.length === 0">
            <td colspan="6" class="empty-msg">{{ t('list.empty') }}</td>
          </tr>
          <tr v-for="item in items" :key="item.id" style="cursor:pointer"
            @click="router.push(`/actions/${item.id}`)">
            <td class="text-muted">{{ item.id }}</td>
            <td class="text-bright">{{ item.name }}</td>
            <td>{{ item.fc_character_name }}</td>
            <td>{{ item.pap_count }}</td>
            <td>
              <span class="badge" :class="item.status === 'active' ? 'badge-active' : 'badge-ended'">
                {{ item.status === 'active' ? t('active') : t('ended') }}
              </span>
            </td>
            <td class="text-muted">{{ formatDate(item.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="pagination" v-if="totalPages() > 1">
      <button class="btn" :disabled="page <= 1" @click="goPage(page - 1)">{{ t('list.prev') }}</button>
      <span class="text-muted">{{ t('list.page', { page, total: totalPages(), count: total }) }}</span>
      <button class="btn" :disabled="page >= totalPages()" @click="goPage(page + 1)">{{ t('list.next') }}</button>
    </div>
    <div v-else class="text-muted" style="margin-top:8px;font-size:12px">{{ t('list.total', { count: total }) }}</div>
  </div>
</template>
