<script setup lang="ts">
import { RouterView } from 'vue-router'
import ConfirmDialog from './components/ConfirmDialog.vue'
import { useConfirmDialog } from './composables/useConfirmDialog'

const { message, _resolve } = useConfirmDialog()

function onConfirm() {
  _resolve.value?.(true)
  message.value = ''
}
function onCancel() {
  _resolve.value?.(false)
  message.value = ''
}
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
  --bg:           #141413;
  --surface:      #30302e;
  --border:       #3d3d3a;
  --text-primary: #faf9f5;
  --text-body:    #b0aea5;
  --text-muted:   #87867f;
  --text-dim:     #5e5d59;
  --brand:        #c96442;
  --brand-light:  #d97757;
  --error-text:   #b53333;
  --error-bg:     #2a1a1a;
  --focus:        #3898ec;
  --radius-sm:    8px;
  --radius-md:    12px;
  --radius-lg:    16px;
  --font-serif:   'Anthropic Serif', Georgia, serif;
  --font-sans:    'Anthropic Sans', system-ui, sans-serif;
  --font-mono:    'Anthropic Mono', monospace;
}

body {
  font-family: var(--font-sans);
  font-size: 14px;
  background: var(--bg);
  color: var(--text-body);
  min-height: 100vh;
  line-height: 1.60;
}

a { color: var(--brand-light); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ── Buttons ───────────────────────────────────────────────── */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-body);
  font-family: var(--font-sans);
  font-size: 1rem;
  cursor: pointer;
  transition: box-shadow 0.15s;
}
.btn:hover:not(:disabled) { box-shadow: 0 0 0 1px #4d4c48; }
.btn:disabled { opacity: 0.45; cursor: not-allowed; }

.btn-primary {
  background: var(--brand);
  border: none;
  color: var(--text-primary);
  box-shadow: var(--brand) 0 0 0 0, var(--brand) 0 0 0 1px;
}
.btn-primary:hover:not(:disabled) { opacity: 0.90; box-shadow: var(--brand) 0 0 0 0, var(--brand) 0 0 0 1px; }

.btn-danger {
  background: var(--error-bg);
  border: 1px solid var(--error-text);
  color: var(--error-text);
}
.btn-danger:hover:not(:disabled) { box-shadow: 0 0 0 1px var(--error-text); }

/* ── Page layout ───────────────────────────────────────────── */
.page { padding: 24px 28px; max-width: 1100px; }

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.page-title {
  font-family: var(--font-serif);
  font-size: 1.3rem;
  color: var(--text-primary);
  font-weight: 500;
}

/* ── Cards / Sections ──────────────────────────────────────── */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 24px;
  margin-bottom: 16px;
}
.card-title {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  font-weight: 500;
  margin-bottom: 14px;
}

/* ── Tables ────────────────────────────────────────────────── */
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td {
  text-align: left;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
}
.data-table th {
  color: var(--text-muted);
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 500;
}
.data-table td { font-size: 0.94rem; color: var(--text-body); }
.data-table tr:last-child td { border-bottom: none; }
.data-table tbody tr:hover { background: rgba(255,255,255,0.03); }

/* ── Status badge ──────────────────────────────────────────── */
.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 24px;
  font-size: 0.75rem;
  font-weight: 500;
  font-family: var(--font-sans);
}
.badge-active { color: var(--brand);      background: rgba(201,100,66,0.15); }
.badge-ended  { color: var(--text-muted); background: rgba(176,174,165,0.10); }

/* ── Forms ─────────────────────────────────────────────────── */
.form-group { margin-bottom: 16px; }
.form-label { display: block; font-size: 0.88rem; color: var(--text-muted); margin-bottom: 6px; }
.form-control {
  width: 100%;
  padding: 8px 12px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-family: var(--font-sans);
  font-size: 1rem;
}
.form-control:focus {
  outline: none;
  border-color: var(--focus);
  box-shadow: 0 0 0 3px rgba(56,152,236,0.15);
}
textarea.form-control { resize: vertical; min-height: 80px; }

/* ── Filter bar ────────────────────────────────────────────── */
.filter-bar { display: flex; gap: 10px; align-items: flex-end; flex-wrap: wrap; margin-bottom: 16px; }
.filter-bar .form-group { margin-bottom: 0; }

/* ── Pagination ────────────────────────────────────────────── */
.pagination { display: flex; gap: 6px; align-items: center; margin-top: 14px; }
.pagination .btn { padding: 4px 10px; }

/* ── Utilities ─────────────────────────────────────────────── */
.text-muted  { color: var(--text-muted); }
.text-bright { color: var(--text-primary); }
.empty-msg   { color: var(--text-dim); text-align: center; padding: 48px 0; font-size: 0.94rem; }
.error-msg {
  color: var(--error-text);
  background: var(--error-bg);
  border: 1px solid var(--error-text);
  border-radius: var(--radius-sm);
  padding: 12px 16px;
  margin-bottom: 12px;
  font-size: 0.94rem;
}
.success-msg {
  color: var(--brand);
  background: rgba(201,100,66,0.08);
  border: 1px solid rgba(201,100,66,0.25);
  border-radius: var(--radius-sm);
  padding: 12px 16px;
  margin-bottom: 12px;
  font-size: 0.94rem;
}
.btn-row { display: flex; gap: 8px; flex-wrap: wrap; }
</style>
