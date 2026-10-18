<template>
  <select
    :value="modelValue ?? ''"
    @change="$emit('update:modelValue', $event.target.value === '' ? null : Number($event.target.value))"
    class="border border-slate-300 rounded-md px-3 py-1.5 text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-navy-600"
  >
    <option value="">通算</option>
    <option v-for="y in years" :key="y" :value="y">{{ y }}年</option>
  </select>
</template>

<script setup>
defineProps({ modelValue: { type: Number, default: null } })
defineEmits(['update:modelValue'])

const currentYear = new Date().getFullYear()
const years = Array.from({ length: 3 }, (_, i) => currentYear - i)
</script>
