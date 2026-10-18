import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'
import PlayersView from '../views/PlayersView.vue'
import GamesView from '../views/GamesView.vue'
import AnalyticsView from '../views/AnalyticsView.vue'
import PlayerDetailView from '../views/PlayerDetailView.vue'
import PitchersView from '../views/PitchersView.vue'
import HistoryView from '../views/HistoryView.vue'
import LoginView from '../views/LoginView.vue'
import { DEMO_MODE } from '../config.js'

const routes = [
  { path: '/login', name: 'login', component: LoginView },
  { path: '/',              name: 'dashboard',     component: DashboardView,    meta: { requiresAuth: true } },
  { path: '/players',       name: 'players',       component: PlayersView,      meta: { requiresAuth: true } },
  { path: '/players/:id',   name: 'playerDetail',  component: PlayerDetailView, meta: { requiresAuth: true } },
  { path: '/games',         name: 'games',         component: GamesView,        meta: { requiresAuth: true } },
  { path: '/analytics',     name: 'analytics',     component: AnalyticsView,    meta: { requiresAuth: true } },
  { path: '/pitchers',      name: 'pitchers',      component: PitchersView,     meta: { requiresAuth: true } },
  { path: '/history',       name: 'history',       component: HistoryView,      meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  if (DEMO_MODE) {
    return to.name === 'login' ? { name: 'dashboard' } : true
  }
  if (to.meta.requiresAuth && !sessionStorage.getItem('id_token')) {
    return { name: 'login' }
  }
})

export default router
