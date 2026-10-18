<template>
  <div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
    <p class="font-semibold mb-1">データの取得に失敗しました</p>
    <p class="text-red-600">APIサーバーが起動しているか確認してください。</p>
    <p v-if="message" class="mt-1 text-red-500 text-xs font-mono">{{ message }}</p>
  </div>
</template>

<script setup>
defineProps({ message: { type: String, default: '' } })
</script>
