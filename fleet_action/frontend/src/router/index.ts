import { createRouter, createWebHashHistory } from 'vue-router'
import ActionsListView from '@/views/ActionsListView.vue'
import CreateActionView from '@/views/CreateActionView.vue'
import ActionDetailView from '@/views/ActionDetailView.vue'

const router = createRouter({
  // Hash history works inside an iframe without server-side routing config
  history: createWebHashHistory(),
  routes: [
    { path: '/', redirect: '/actions' },
    { path: '/actions', component: ActionsListView },
    { path: '/actions/create', component: CreateActionView },
    { path: '/actions/:id', component: ActionDetailView },
  ],
})

export default router
