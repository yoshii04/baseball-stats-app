<template>
  <div class="min-h-screen bg-slate-50">
    <div v-if="DEMO_MODE" class="bg-amber-100 text-amber-900 text-xs text-center py-1">
      デモ表示: 架空のチーム・選手・試合による合成データです（実データではありません）
    </div>
    <NavBar />
    <main class="max-w-7xl mx-auto px-4 py-8">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import NavBar from './components/NavBar.vue'
import { DEMO_MODE } from './config.js'
</script>
