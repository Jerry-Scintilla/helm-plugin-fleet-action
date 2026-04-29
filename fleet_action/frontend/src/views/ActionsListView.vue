<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api, type ActionItem } from '@/api'

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
  return new Date(dt).toLocaleString('zh-CN', { hour12: false })
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <span class="page-title">舰队行动记录</span>
      <button class="btn btn-primary" @click="router.push('/actions/create')">+ 新建行动</button>
    </div>

    <!-- Filter bar -->
    <div class="filter-bar">
      <div class="form-group">
        <label class="form-label">状态</label>
        <select class="form-control" v-model="filterStatus" style="width:120px">
          <option value="">全部</option>
          <option value="active">进行中</option>
          <option value="ended">已结束</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">指挥官</label>
        <input class="form-control" v-model="filterFc" placeholder="模糊搜索" style="width:160px"
          @keyup.enter="applyFilter" />
      </div>
      <button class="btn btn-primary" @click="applyFilter" :disabled="loading">搜索</button>
      <button class="btn" @click="resetFilter" :disabled="loading">重置</button>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>

    <div class="card" style="padding:0; overflow:hidden">
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>行动名称</th>
            <th>舰队指挥官</th>
            <th>PAP 数</th>
            <th>状态</th>
            <th>创建时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="6" class="empty-msg">加载中…</td>
          </tr>
          <tr v-else-if="items.length === 0">
            <td colspan="6" class="empty-msg">暂无行动记录</td>
          </tr>
          <tr v-for="item in items" :key="item.id" style="cursor:pointer"
            @click="router.push(`/actions/${item.id}`)">
            <td class="text-muted">{{ item.id }}</td>
            <td class="text-bright">{{ item.name }}</td>
            <td>{{ item.fc_character_name }}</td>
            <td>{{ item.pap_count }}</td>
            <td>
              <span class="badge" :class="item.status === 'active' ? 'badge-active' : 'badge-ended'">
                {{ item.status === 'active' ? '进行中' : '已结束' }}
              </span>
            </td>
            <td class="text-muted">{{ formatDate(item.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="pagination" v-if="totalPages() > 1">
      <button class="btn" :disabled="page <= 1" @click="goPage(page - 1)">‹ 上一页</button>
      <span class="text-muted">第 {{ page }} / {{ totalPages() }} 页，共 {{ total }} 条</span>
      <button class="btn" :disabled="page >= totalPages()" @click="goPage(page + 1)">下一页 ›</button>
    </div>
    <div v-else class="text-muted" style="margin-top:8px;font-size:12px">共 {{ total }} 条记录</div>
  </div>
</template>
