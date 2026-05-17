<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, type ActionDetail, type FleetMember, type IssuePapResult } from '@/api'
import { useConfirmDialog } from '@/composables/useConfirmDialog'

const route = useRoute()
const router = useRouter()
const actionId = Number(route.params.id)

const { confirm } = useConfirmDialog()

const action = ref<ActionDetail | null>(null)
const loading = ref(true)
const error = ref('')

// Members & PAP
const members = ref<FleetMember[]>([])
const membersLoading = ref(false)
const membersError = ref('')
const membersLoaded = ref(false)

const registeredCount = computed(() => members.value.filter(m => m.is_registered).length)

const papResult = ref<IssuePapResult | null>(null)
const papLoading = ref(false)
const papError = ref('')

async function loadAction() {
  loading.value = true
  error.value = ''
  try {
    action.value = await api.getAction(actionId)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

async function endAction() {
  if (!(await confirm('确定结束此行动？结束后无法继续发放 PAP。'))) return
  try {
    await api.endAction(actionId)
    await loadAction()
  } catch (e) {
    error.value = (e as Error).message
  }
}

async function deleteAction() {
  if (!(await confirm('确定删除此行动？此操作不可撤销。'))) return
  try {
    await api.deleteAction(actionId)
    router.push('/actions')
  } catch (e) {
    error.value = (e as Error).message
  }
}

async function fetchMembers() {
  membersLoading.value = true
  membersError.value = ''
  try {
    members.value = await api.getMembers(actionId)
    membersLoaded.value = true
  } catch (e) {
    membersError.value = (e as Error).message
  } finally {
    membersLoading.value = false
  }
}

async function issuePap() {
  if (!action.value) return
  if (!membersLoaded.value) {
    papError.value = '请先查询当前舰队成员'
    return
  }
  papLoading.value = true
  papError.value = ''
  papResult.value = null
  try {
    papResult.value = await api.issuePap(actionId, {
      action_id: actionId,
      fc_character_id: action.value.fc_character_id,
      update_motd: true,
    })
    // Refresh PAP records
    await loadAction()
  } catch (e) {
    papError.value = (e as Error).message
  } finally {
    papLoading.value = false
  }
}

function formatDate(dt: string | null) {
  if (!dt) return '—'
  return new Date(dt).toLocaleString('zh-CN', { hour12: false })
}

onMounted(loadAction)
</script>

<template>
  <div class="page">
    <!-- Header -->
    <div class="page-header">
      <div style="display:flex;align-items:center;gap:12px">
        <button class="btn" @click="router.push('/actions')" style="padding:4px 10px">← 返回</button>
        <span class="page-title">行动详情</span>
      </div>
    </div>

    <div v-if="loading" class="text-muted">加载中…</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>

    <template v-if="action">

      <!-- ── 区块 A：基本信息 ──────────────────────────────────── -->
      <div class="card">
        <div class="card-title">基本信息</div>
        <table style="width:100%;border-collapse:collapse">
          <tbody>
            <tr>
              <td class="info-label">行动名称</td>
              <td class="text-bright">{{ action.name }}</td>
              <td class="info-label">状态</td>
              <td>
                <span class="badge" :class="action.status === 'active' ? 'badge-active' : 'badge-ended'">
                  {{ action.status === 'active' ? '进行中' : '已结束' }}
                </span>
              </td>
            </tr>
            <tr>
              <td class="info-label">舰队指挥官</td>
              <td>{{ action.fc_character_name }}</td>
              <td class="info-label">创建时间</td>
              <td class="text-muted">{{ formatDate(action.created_at) }}</td>
            </tr>
            <tr v-if="action.description">
              <td class="info-label">行动描述</td>
              <td colspan="3">{{ action.description }}</td>
            </tr>
            <tr v-if="action.ended_at">
              <td class="info-label">结束时间</td>
              <td colspan="3" class="text-muted">{{ formatDate(action.ended_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- ── 区块 B：操作按钮 ──────────────────────────────────── -->
      <div class="card">
        <div class="card-title">行动操作</div>
        <div class="btn-row">
          <button v-if="action.status === 'active'" class="btn btn-primary" @click="endAction">
            ⏹ 结束行动
          </button>
          <button class="btn btn-danger" @click="deleteAction">
            🗑 删除行动
          </button>
        </div>
      </div>

      <!-- ── 区块 C：舰队成员预览 + 发放 PAP（仅 active）──────── -->
      <div class="card" v-if="action.status === 'active'">
        <div class="card-title">发放 PAP 出勤记录</div>

        <div class="btn-row" style="margin-bottom:14px">
          <button class="btn" :disabled="membersLoading" @click="fetchMembers">
            {{ membersLoading ? '查询中…' : '查询当前舰队成员' }}
          </button>
          <button class="btn btn-primary" :disabled="!membersLoaded || papLoading" @click="issuePap">
            {{ papLoading ? '发放中…' : '向当前成员发放 PAP' }}
          </button>
        </div>

        <div v-if="membersError" class="error-msg">{{ membersError }}</div>
        <div v-if="papError" class="error-msg">{{ papError }}</div>

        <div v-if="papResult" class="success-msg">
          已发放 {{ papResult.issued_count }} 人 PAP。
          <span v-if="papResult.motd_updated">MOTD 已更新。</span>
          <span v-else-if="papResult.issued_count > 0">MOTD 更新失败（不影响记录）。</span>
        </div>

        <template v-if="membersLoaded">
          <div v-if="members.length === 0" class="empty-msg">当前舰队无成员</div>
          <template v-else>
            <div class="text-muted" style="font-size:12px;margin-bottom:8px">
              当前舰队成员：{{ members.length }} 人
              <span class="text-muted">（已注册 {{ registeredCount }} 人）</span>
            </div>
            <table class="data-table">
              <thead>
                <tr>
                  <th>角色名</th>
                  <th>角色 ID</th>
                  <th>注册状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="m in members" :key="m.character_id">
                  <td :class="{ 'text-bright': m.character_name, 'text-muted': !m.character_name }">
                    {{ m.character_name || '未知' }}
                  </td>
                  <td class="text-muted">{{ m.character_id }}</td>
                  <td>
                    <span v-if="m.is_registered" class="badge badge-active">已注册</span>
                    <span v-else class="badge badge-ended">未注册</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </template>
        </template>
      </div>

      <!-- ── 区块 D：PAP 记录 ──────────────────────────────────── -->
      <div class="card">
        <div class="card-title">PAP 出勤记录（{{ action.pap_count }} 人）</div>
        <div v-if="action.pap_records.length === 0" class="empty-msg">暂无 PAP 记录</div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>角色名</th>
              <th>角色 ID</th>
              <th>发放时间</th>
              <th>发放人 ID</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in action.pap_records" :key="p.id">
              <td class="text-bright">{{ p.character_name }}</td>
              <td class="text-muted">{{ p.character_id }}</td>
              <td class="text-muted">{{ formatDate(p.issued_at) }}</td>
              <td class="text-muted">{{ p.issued_by_character_id }}</td>
            </tr>
          </tbody>
        </table>
      </div>

    </template>
  </div>
</template>

<style scoped>
.info-label {
  color: var(--text-muted);
  font-size: 0.8rem;
  padding: 7px 16px 7px 0;
  white-space: nowrap;
  width: 90px;
  vertical-align: top;
}
</style>
