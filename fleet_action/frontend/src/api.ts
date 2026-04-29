// Module-level SDK context — set once by HelmSDK.init(), updated on token refresh
let _token = ''
let _apiBase = ''
const BASE = '/api/v1/plugins/fleet-action'

export function initSDK(token: string, apiBase: string) {
  _token = token
  _apiBase = apiBase
}

export function updateToken(token: string) {
  _token = token
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
declare const HelmSDK: any

async function request<T = unknown>(method: string, path: string, body?: unknown): Promise<T> {
  const r = await fetch(_apiBase + BASE + path, {
    method,
    headers: {
      Authorization: 'Bearer ' + _token,
      'Content-Type': 'application/json',
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  if (r.status === 401) {
    HelmSDK.requestTokenRefresh()
    throw new Error('401')
  }
  if (!r.ok) {
    const text = await r.text().catch(() => '')
    throw new Error(`HTTP ${r.status}${text ? ': ' + text : ''}`)
  }
  if (r.status === 204) return null as T
  return r.json() as Promise<T>
}

// ── Types ──────────────────────────────────────────────────────────────────────

export interface Character {
  label: string
  value: number
}

export interface ActionItem {
  id: number
  name: string
  description: string
  fleet_id: number | null
  fc_character_id: number
  fc_character_name: string
  status: 'active' | 'ended'
  created_at: string
  ended_at: string | null
  pap_count: number
}

export interface PapRecord {
  id: number
  character_id: number
  character_name: string
  issued_at: string
  issued_by_character_id: number
}

export interface ActionDetail extends ActionItem {
  pap_records: PapRecord[]
}

export interface ActionsPage {
  items: ActionItem[]
  total: number
}

export interface FleetMember {
  character_id: number
  character_name: string
  ship_type_id?: number
}

export interface IssuePapResult {
  action_id: number
  issued_count: number
  member_ids: number[]
  motd_updated: boolean
}

// ── API calls ──────────────────────────────────────────────────────────────────

export const api = {
  getCharacters: () => request<Character[]>('GET', '/characters'),

  listActions: (params: Record<string, string>) =>
    request<ActionsPage>('GET', '/actions?' + new URLSearchParams(params)),

  createAction: (body: { name: string; description: string; fc_character_id: number }) =>
    request<ActionItem>('POST', '/actions', body),

  getAction: (id: number) => request<ActionDetail>('GET', `/actions/${id}`),

  endAction: (id: number) => request('POST', `/actions/${id}`),

  deleteAction: (id: number) => request('DELETE', `/actions/${id}`),

  getMembers: (id: number) => request<FleetMember[]>('GET', `/actions/${id}/members`),

  issuePap: (id: number, body: { action_id: number; fc_character_id: number; update_motd: boolean }) =>
    request<IssuePapResult>('POST', `/actions/${id}/pap`, body),
}
