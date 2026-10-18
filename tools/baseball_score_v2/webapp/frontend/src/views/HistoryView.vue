<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-slate-800">実行履歴</h1>
      <button
        @click="fetch"
        class="px-3 py-1.5 text-sm border border-slate-300 rounded-md text-slate-700 bg-white hover:bg-slate-50 transition-colors"
      >
        更新
      </button>
    </div>

    <!-- フィルター -->
    <div class="flex flex-wrap items-center gap-3 mb-6">
      <div class="flex items-center gap-2">
        <label class="text-sm text-slate-600">日付</label>
        <input
          v-model="filterDate"
          type="date"
          @change="fetch"
          class="border border-slate-300 rounded-md px-3 py-1.5 text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-navy-600"
        />
      </div>
      <div class="flex items-center gap-2">
        <label class="text-sm text-slate-600">ステップ</label>
        <select
          v-model="filterStep"
          @change="fetch"
          class="border border-slate-300 rounded-md px-3 py-1.5 text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-navy-600"
        >
          <option value="">全ステップ</option>
          <option value="validate">validate</option>
          <option value="generate">generate</option>
          <option value="import_db">import_db</option>
          <option value="analytics">analytics</option>
        </select>
      </div>
      <div class="flex items-center gap-2">
        <label class="text-sm text-slate-600">表示件数</label>
        <select
          v-model="filterLast"
          @change="fetch"
          class="border border-slate-300 rounded-md px-3 py-1.5 text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-navy-600"
        >
          <option :value="null">全件</option>
          <option :value="20">20件</option>
          <option :value="50">50件</option>
          <option :value="100">100件</option>
        </select>
      </div>
      <button
        v-if="filterDate || filterStep || filterLast"
        @click="clearFilters"
        class="text-sm text-slate-400 hover:text-slate-600 underline"
      >
        クリア
      </button>
    </div>

    <LoadingSpinner v-if="loading" />
    <ErrorAlert v-else-if="error" :message="error" />

    <template v-else>
      <p v-if="records.length === 0" class="text-slate-500 text-sm text-center py-12">
        該当する実行履歴がありません。
      </p>

      <template v-else>
        <!-- run_id ごとにグループ化して表示 -->
        <div
          v-for="group in groupedRecords"
          :key="group.runId"
          class="mb-4 bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden"
        >
          <!-- グループヘッダー -->
          <div class="flex items-center justify-between px-4 py-2.5 bg-slate-50 border-b border-slate-200">
            <span class="text-xs font-mono text-slate-500">{{ group.runId }}</span>
            <span class="text-xs text-slate-400">{{ formatDate(group.startedAt) }}</span>
          </div>

          <!-- ステップ一覧 -->
          <table class="w-full text-sm">
            <tbody>
              <tr
                v-for="r in group.records"
                :key="r.timestamp + r.step"
                class="border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors"
              >
                <!-- ステータス -->
                <td class="px-4 py-2.5 w-20">
                  <span
                    :class="statusClass(r.status)"
                    class="inline-block px-2 py-0.5 rounded text-xs font-semibold"
                  >
                    {{ statusLabel(r.status) }}
                  </span>
                </td>
                <!-- 時刻 -->
                <td class="px-2 py-2.5 w-20 text-xs text-slate-400 font-mono">
                  {{ formatTime(r.timestamp) }}
                </td>
                <!-- ラベル -->
                <td class="px-2 py-2.5 text-slate-700">
                  {{ r.label }}
                </td>
                <!-- 年度 -->
                <td class="px-2 py-2.5 w-20 text-xs text-slate-400 text-right">
                  <span v-if="r.year">{{ r.year }}年</span>
                </td>
                <!-- エラー -->
                <td class="px-4 py-2.5">
                  <span v-if="r.error" class="text-xs text-red-500">{{ r.error }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <p class="text-xs text-slate-400 text-right mt-2">合計 {{ records.length }} 件</p>
      </template>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { historyApi } from '../api/index.js'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import ErrorAlert from '../components/ErrorAlert.vue'

const records   = ref([])
const loading   = ref(false)
const error     = ref(null)

const filterDate = ref('')
const filterStep = ref('')
const filterLast = ref(null)

async function fetch() {
  loading.value = true
  error.value   = null
  try {
    const res = await historyApi.list({
      date: filterDate.value || undefined,
      step: filterStep.value || undefined,
      last: filterLast.value || undefined,
    })
    records.value = res.records
  } catch (e) {
    error.value = '実行履歴の取得に失敗しました'
  } finally {
    loading.value = false
  }
}

function clearFilters() {
  filterDate.value = ''
  filterStep.value = ''
  filterLast.value = null
  fetch()
}

/** run_id でグループ化 */
const groupedRecords = computed(() => {
  const groups = []
  const seen = new Map()
  for (const r of records.value) {
    const id = r.run_id ?? 'unknown'
    if (!seen.has(id)) {
      const group = { runId: id, startedAt: r.timestamp, records: [] }
      seen.set(id, group)
      groups.push(group)
    }
    seen.get(id).records.push(r)
  }
  return groups
})

function formatDate(ts) {
  if (!ts) return ''
  return ts.slice(0, 10)
}

function formatTime(ts) {
  if (!ts) return ''
  return ts.slice(11, 19)
}

function statusLabel(status) {
  return { OK: '成功', NG: '失敗', SKIP: 'スキップ' }[status] ?? status
}

function statusClass(status) {
  return {
    OK:   'bg-green-100 text-green-700',
    NG:   'bg-red-100 text-red-700',
    SKIP: 'bg-slate-100 text-slate-500',
  }[status] ?? 'bg-slate-100 text-slate-500'
}

onMounted(fetch)
</script>
