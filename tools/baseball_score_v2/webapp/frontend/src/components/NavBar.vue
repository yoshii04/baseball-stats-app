<template>
  <nav class="bg-navy-700 text-white shadow-lg">
    <div class="max-w-7xl mx-auto px-4">
      <div class="flex items-center justify-between h-16">

        <!-- ロゴ -->
        <RouterLink
          to="/"
          class="flex items-center gap-2 text-lg font-bold hover:opacity-80 transition-opacity"
        >
          <span class="text-2xl">⚾</span>
          <span>{{ TEAM_NAME }} 野球成績管理</span>
        </RouterLink>

        <!-- ナビリンク -->
        <div class="flex items-center gap-1">
          <RouterLink
            v-for="link in navLinks"
            :key="link.to"
            :to="link.to"
            class="px-4 py-2 rounded-md text-sm font-medium transition-colors"
            :class="isActive(link.to)
              ? 'bg-white text-navy-700 font-semibold'
              : 'text-slate-200 hover:bg-navy-600 hover:text-white'"
          >
            {{ link.label }}
          </RouterLink>
        </div>

      </div>
    </div>
  </nav>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { TEAM_NAME } from '../config.js'

const route = useRoute()

const navLinks = [
  { to: '/',          label: 'ダッシュボード' },
  { to: '/players',   label: '打撃成績' },
  { to: '/pitchers',  label: '投手成績' },
  { to: '/games',     label: '試合一覧' },
  { to: '/analytics', label: '分析' },
  { to: '/history',   label: '実行履歴' },
]

function isActive(path) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>
