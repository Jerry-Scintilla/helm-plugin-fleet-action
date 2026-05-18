<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, type ActionDetail, type FleetMember, type IssuePapResult } from '@/api'
import { useConfirmDialog } from '@/composables/useConfirmDialog'
import { t, dateLocale } from '@/i18n'

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
const papCount = ref(1)
const lastPapCount = ref(1)

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
  if (!(await confirm(t('detail.confirm.end')))) return
  try {
    await api.endAction(actionId)
    await loadAction()
  } catch (e) {
    error.value = (e as Error).message
  }
}

async function deleteAction() {
  if (!(await confirm(t('detail.confirm.delete')))) return
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
    papError.value = t('pap.err.noFetch')
    return
  }
  papLoading.value = true
  papError.value = ''
  papResult.value = null
  lastPapCount.value = papCount.value
  try {
    papResult.value = await api.issuePap(actionId, {
      action_id: actionId,
      fc_character_id: action.value.fc_character_id,
      update_motd: true,
      pap_count: papCount.value,
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
  return new Date(dt).toLocaleString(dateLocale(), { hour12: false })
}

onMounted(loadAction)
</script>

<template>
  <div class="page">
    <!-- Header -->
    <div class="page-header">
      <div style="display:flex;align-items:center;gap:12px">
        <button class="btn" @click="router.push('/actions')" style="padding:4px 10px">{{ t('back') }}</button>
        <span class="page-title">{{ t('detail.title') }}</span>
      </div>
    </div>

    <div v-if="loading" class="text-muted">{{ t('loading') }}</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>

    <template v-if="action">

      <!-- ── Section A: Basic Info ───────────────────────────────── -->
      <div class="card">
        <div class="card-title">{{ t('detail.info') }}</div>
        <table style="width:100%;border-collapse:collapse">
          <tbody>
            <tr>
              <td class="info-label">{{ t('detail.field.name') }}</td>
              <td class="text-bright">{{ action.name }}</td>
              <td class="info-label">{{ t('detail.field.status') }}</td>
              <td>
                <span class="badge" :class="action.status === 'active' ? 'badge-active' : 'badge-ended'">
                  {{ action.status === 'active' ? t('active') : t('ended') }}
                </span>
              </td>
            </tr>
            <tr>
              <td class="info-label">{{ t('detail.field.fc') }}</td>
              <td>{{ action.fc_character_name }}</td>
              <td class="info-label">{{ t('detail.field.created') }}</td>
              <td class="text-muted">{{ formatDate(action.created_at) }}</td>
            </tr>
            <tr v-if="action.description">
              <td class="info-label">{{ t('detail.field.desc') }}</td>
              <td colspan="3">{{ action.description }}</td>
            </tr>
            <tr v-if="action.ended_at">
              <td class="info-label">{{ t('detail.field.ended') }}</td>
              <td colspan="3" class="text-muted">{{ formatDate(action.ended_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- ── Section B: Action Buttons ─────────────────────────── -->
      <div class="card">
        <div class="card-title">{{ t('detail.actions') }}</div>
        <div class="btn-row">
          <button v-if="action.status === 'active'" class="btn btn-primary" @click="endAction">
            {{ t('detail.btn.end') }}
          </button>
          <button class="btn btn-danger" @click="deleteAction">
            {{ t('detail.btn.delete') }}
          </button>
        </div>
      </div>

      <!-- ── Section C: Fleet Members + Issue PAP (active only) ── -->
      <div class="card" v-if="action.status === 'active'">
        <div class="card-title">{{ t('pap.section') }}</div>

        <div class="btn-row" style="margin-bottom:14px;align-items:center">
          <button class="btn" :disabled="membersLoading" @click="fetchMembers">
            {{ membersLoading ? t('pap.fetching') : t('pap.fetch') }}
          </button>
          <label style="display:flex;align-items:center;gap:6px;color:var(--text-muted);font-size:0.85rem">
            {{ t('pap.perPerson') }}
            <input
              v-model.number="papCount"
              type="number"
              min="1"
              max="10"
              style="width:52px;padding:4px 6px;background:var(--bg-card);border:1px solid var(--border);border-radius:4px;color:var(--text-bright);text-align:center"
            />
            {{ t('pap.unit') }}
          </label>
          <button class="btn btn-primary" :disabled="!membersLoaded || papLoading" @click="issuePap">
            {{ papLoading ? t('pap.issuing') : t('pap.issue') }}
          </button>
        </div>

        <div v-if="membersError" class="error-msg">{{ membersError }}</div>
        <div v-if="papError" class="error-msg">{{ papError }}</div>

        <div v-if="papResult" class="success-msg">
          <template v-if="papResult.issued_count === 0">
            {{ t('pap.result.noChange', { n: lastPapCount }) }}
          </template>
          <template v-else>
            <span v-if="papResult.new_member_count > 0">{{ t('pap.result.newMembers', { count: papResult.new_member_count, n: lastPapCount }) }}</span>
            <span v-if="papResult.overwritten_count > 0">{{ t('pap.result.overwritten', { count: papResult.overwritten_count, n: lastPapCount }) }}</span>
            <span v-if="papResult.motd_updated">{{ t('pap.result.motdOk') }}</span>
            <span v-else>{{ t('pap.result.motdFail') }}</span>
          </template>
        </div>

        <template v-if="membersLoaded">
          <div v-if="members.length === 0" class="empty-msg">{{ t('pap.noMembers') }}</div>
          <template v-else>
            <div class="text-muted" style="font-size:12px;margin-bottom:8px">
              {{ t('pap.memberCount', { total: members.length }) }}
              <span class="text-muted">{{ t('pap.registeredCount', { count: registeredCount }) }}</span>
            </div>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ t('pap.col.name') }}</th>
                  <th>{{ t('pap.col.id') }}</th>
                  <th>{{ t('pap.col.reg') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="m in members" :key="m.character_id">
                  <td :class="{ 'text-bright': m.character_name, 'text-muted': !m.character_name }">
                    {{ m.character_name || t('unknown') }}
                  </td>
                  <td class="text-muted">{{ m.character_id }}</td>
                  <td>
                    <span v-if="m.is_registered" class="badge badge-active">{{ t('registered') }}</span>
                    <span v-else class="badge badge-ended">{{ t('unregistered') }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </template>
        </template>
      </div>

      <!-- ── Section D: PAP Records ─────────────────────────────── -->
      <div class="card">
        <div class="card-title">{{ t('records.title', { count: action.pap_count }) }}</div>
        <div v-if="action.pap_records.length === 0" class="empty-msg">{{ t('records.empty') }}</div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>{{ t('records.col.name') }}</th>
              <th>{{ t('records.col.id') }}</th>
              <th>{{ t('records.col.time') }}</th>
              <th>{{ t('records.col.by') }}</th>
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
