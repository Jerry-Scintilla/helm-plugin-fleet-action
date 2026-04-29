<script setup lang="ts">
import { RouterView } from 'vue-router'
import ConfirmDialog from './components/ConfirmDialog.vue'
import { useConfirmDialog } from './composables/useConfirmDialog'

const { message, _resolve } = useConfirmDialog()

function onConfirm() { _resolve.value?.(true) }
function onCancel() { _resolve.value?.(false) }
</script>

<template>
  <ConfirmDialog
    :message="message"
    :visible="!!message"
    @confirm="onConfirm"
    @cancel="onCancel"
  />
  <RouterView />
</template>

<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #1e1e1c;
  --surface: #26261f;
  --surface2: #2c2c24;
  --border: #30302e;
  --text: #b0aea5;
  --text-bright: #f5f4ed;
  --muted: #5e5d59;
  --primary: #4a7c59;
  --primary-hover: #3d6849;
  --danger: #8b2020;
  --danger-hover: #6e1919;
  --badge-active: #6abf69;
  --badge-ended: #87867f;
  --radius: 6px;
}

body {
  font-family: 'Segoe UI', system-ui, sans-serif;
  font-size: 14px;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
}

a { color: var(--badge-active); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ── Buttons ───────────────────────────────────────────────── */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface2);
  color: var(--text);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.btn:hover { background: var(--surface); border-color: #484840; }
.btn:disabled { opacity: 0.45; cursor: not-allowed; }

.btn-primary { background: var(--primary); border-color: var(--primary); color: #fff; }
.btn-primary:hover:not(:disabled) { background: var(--primary-hover); border-color: var(--primary-hover); }

.btn-danger { background: var(--danger); border-color: var(--danger); color: #fff; }
.btn-danger:hover:not(:disabled) { background: var(--danger-hover); border-color: var(--danger-hover); }

/* ── Page layout ───────────────────────────────────────────── */
.page { padding: 24px 28px; max-width: 1100px; }

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.page-title { font-size: 1.3rem; color: var(--text-bright); font-weight: 600; }

/* ── Cards / Sections ──────────────────────────────────────── */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px 20px;
  margin-bottom: 16px;
}
.card-title {
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--muted);
  margin-bottom: 14px;
}

/* ── Tables ────────────────────────────────────────────────── */
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td {
  text-align: left;
  padding: 9px 12px;
  border-bottom: 1px solid var(--border);
}
.data-table th {
  color: var(--muted);
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}
.data-table tr:last-child td { border-bottom: none; }
.data-table tbody tr:hover { background: var(--surface2); }

/* ── Status badge ──────────────────────────────────────────── */
.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 99px;
  font-size: 0.75rem;
  font-weight: 600;
}
.badge-active { color: var(--badge-active); background: rgba(106,191,105,0.12); }
.badge-ended  { color: var(--badge-ended);  background: rgba(135,134,127,0.12); }

/* ── Forms ─────────────────────────────────────────────────── */
.form-group { margin-bottom: 16px; }
.form-label { display: block; font-size: 0.82rem; color: var(--muted); margin-bottom: 6px; }
.form-control {
  width: 100%;
  padding: 7px 10px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text-bright);
  font-size: 13px;
}
.form-control:focus { outline: none; border-color: var(--primary); }
textarea.form-control { resize: vertical; min-height: 80px; }

/* ── Filter bar ────────────────────────────────────────────── */
.filter-bar { display: flex; gap: 10px; align-items: flex-end; flex-wrap: wrap; margin-bottom: 16px; }
.filter-bar .form-group { margin-bottom: 0; }

/* ── Pagination ────────────────────────────────────────────── */
.pagination { display: flex; gap: 6px; align-items: center; margin-top: 14px; }
.pagination .btn { padding: 4px 10px; }

/* ── Utilities ─────────────────────────────────────────────── */
.text-muted { color: var(--muted); }
.text-bright { color: var(--text-bright); }
.empty-msg { color: var(--muted); text-align: center; padding: 32px 0; }
.error-msg {
  color: #e07070;
  background: #2a1a1a;
  border: 1px solid #5a2020;
  border-radius: var(--radius);
  padding: 12px 16px;
  margin-bottom: 12px;
}
.success-msg {
  color: #6abf69;
  background: rgba(106,191,105,0.08);
  border: 1px solid rgba(106,191,105,0.25);
  border-radius: var(--radius);
  padding: 12px 16px;
  margin-bottom: 12px;
}
.btn-row { display: flex; gap: 8px; flex-wrap: wrap; }
</style>
