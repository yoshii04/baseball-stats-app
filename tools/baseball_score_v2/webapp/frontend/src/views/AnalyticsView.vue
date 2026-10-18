<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-slate-800">分析</h1>
      <YearSelector v-model="year" @update:modelValue="fetchAll" />
    </div>

    <LoadingSpinner v-if="loading" />
    <ErrorAlert v-else-if="error" :message="error" />

    <template v-else>
      <!-- チーム成績サマリー -->
      <div v-if="teamRecord.game_count != null" class="mb-6 bg-slate-50 border border-slate-200 rounded-lg p-4">
        <h2 class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">チーム成績</h2>
        <div class="flex flex-wrap gap-6 text-sm mb-3">
          <div class="text-center">
            <p class="text-xs text-slate-400 mb-1">試合</p>
            <p class="text-xl font-bold text-slate-700">{{ teamRecord.game_count }}</p>
          </div>
          <div class="text-center">
            <p class="text-xs text-slate-400 mb-1">勝</p>
            <p class="text-xl font-bold text-green-600">{{ teamRecord.wins }}</p>
          </div>
          <div class="text-center">
            <p class="text-xs text-slate-400 mb-1">負</p>
            <p class="text-xl font-bold text-red-500">{{ teamRecord.losses }}</p>
          </div>
          <div class="text-center">
            <p class="text-xs text-slate-400 mb-1">分</p>
            <p class="text-xl font-bold text-amber-500">{{ teamRecord.draws }}</p>
          </div>
          <div class="w-px bg-slate-200 self-stretch mx-1"></div>
          <div class="text-center">
            <p class="text-xs text-slate-400 mb-1">得点</p>
            <p class="text-xl font-bold text-slate-700">{{ teamRecord.runs_scored }}</p>
          </div>
          <div class="text-center">
            <p class="text-xs text-slate-400 mb-1">失点</p>
            <p class="text-xl font-bold text-slate-500">{{ teamRecord.runs_allowed }}</p>
          </div>
        </div>
        <!-- 試合別成績 -->
        <div
          v-if="teamRecord.by_game_number && teamRecord.by_game_number.length > 1"
          class="border-t border-slate-200 pt-2 space-y-1"
        >
          <div
            v-for="gn in teamRecord.by_game_number"
            :key="gn.game_number"
            class="flex items-center gap-4 text-sm"
          >
            <span class="text-xs font-semibold text-slate-400 w-16 shrink-0">第{{ gn.game_number }}試合</span>
            <span class="font-bold text-green-600">○{{ gn.wins }}</span>
            <span class="font-bold text-red-500">×{{ gn.losses }}</span>
            <span class="font-bold text-amber-500">△{{ gn.draws }}</span>
            <span class="text-slate-300 mx-1">|</span>
            <span class="text-slate-500 text-xs">{{ gn.game_count }}試合</span>
            <span class="text-slate-400 text-xs">得点{{ gn.runs_scored }} 失点{{ gn.runs_allowed }}</span>
          </div>
        </div>
      </div>

      <!-- タブ切り替え -->
      <div class="flex gap-1 mb-6 border-b border-slate-200">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          @click="activeTab = tab.key"
          class="px-4 py-2 text-sm font-medium rounded-t-md transition-colors"
          :class="activeTab === tab.key
            ? 'bg-white border border-b-white border-slate-200 text-navy-700 -mb-px'
            : 'text-slate-500 hover:text-slate-700'"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- 打球方向タブ -->
      <div v-if="activeTab === 'direction'" class="space-y-6">
        <!-- 打球方向グラフ -->
        <div v-if="directions.length > 0" class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <h2 class="font-semibold text-slate-700 mb-4">打球方向グラフ（割合）</h2>
          <div :style="{ height: directionChartHeight }">
            <Bar :data="directionChartData" :options="directionChartOptions" />
          </div>
        </div>

        <!-- 打球方向テーブル -->
        <div class="bg-white rounded-lg shadow-sm border border-slate-200">
          <div class="px-6 py-4 border-b border-slate-100">
            <h2 class="font-semibold text-slate-700">打球方向分析</h2>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="bg-slate-50 text-slate-500 text-xs uppercase">
                <tr>
                  <th class="px-4 py-3 text-left">選手名</th>
                  <th class="px-4 py-3 text-right">右(9)</th>
                  <th class="px-4 py-3 text-right">右中</th>
                  <th class="px-4 py-3 text-right">中</th>
                  <th class="px-4 py-3 text-right">左中</th>
                  <th class="px-4 py-3 text-right">左(7)</th>
                  <th class="px-4 py-3 text-right">合計</th>
                  <th class="px-4 py-3 text-right">右%</th>
                  <th class="px-4 py-3 text-right">右中%</th>
                  <th class="px-4 py-3 text-right">中%</th>
                  <th class="px-4 py-3 text-right">左中%</th>
                  <th class="px-4 py-3 text-right">左%</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                <tr
                  v-for="p in directions"
                  :key="p.player_id"
                  class="hover:bg-slate-50"
                >
                  <td class="px-4 py-3 font-medium text-slate-800">{{ p.player_name }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ p.right_9 }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ p.right_center }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ p.center_field }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ p.left_center }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ p.left_7 }}</td>
                  <td class="px-4 py-3 text-right font-medium text-slate-700">{{ p.total }}</td>
                  <td class="px-4 py-3 text-right text-slate-500">{{ p.pct_right_9 }}%</td>
                  <td class="px-4 py-3 text-right text-slate-500">{{ p.pct_right_center }}%</td>
                  <td class="px-4 py-3 text-right text-slate-500">{{ p.pct_center }}%</td>
                  <td class="px-4 py-3 text-right text-slate-500">{{ p.pct_left_center }}%</td>
                  <td class="px-4 py-3 text-right text-slate-500">{{ p.pct_left_7 }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 累積成績推移タブ -->
      <div v-if="activeTab === 'trend'" class="space-y-6">
        <!-- 選手選択 -->
        <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-4 flex items-center gap-4">
          <span class="font-semibold text-slate-700 text-sm">選手選択</span>
          <select
            v-model="selectedPlayerId"
            class="border border-slate-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-navy-600"
          >
            <option :value="null">— 選手を選択 —</option>
            <option v-for="p in playerList" :key="p.player_id" :value="p.player_id">
              {{ p.player_name }}
            </option>
          </select>
        </div>

        <!-- 累積OPS推移グラフ -->
        <div v-if="trendFiltered.length > 0" class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <h2 class="font-semibold text-slate-700 mb-4">累積打率・OPS推移グラフ</h2>
          <div style="height: 300px;">
            <Line :data="trendChartData" :options="trendChartOptions" />
          </div>
        </div>

        <!-- 累積成績推移テーブル -->
        <div class="bg-white rounded-lg shadow-sm border border-slate-200">
          <div class="px-6 py-4 border-b border-slate-100">
            <h2 class="font-semibold text-slate-700">累積打率・OPS推移</h2>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="bg-slate-50 text-slate-500 text-xs uppercase">
                <tr>
                  <th class="px-4 py-3 text-left">選手名</th>
                  <th class="px-4 py-3 text-left">試合日</th>
                  <th class="px-4 py-3 text-left">対戦相手</th>
                  <th class="px-4 py-3 text-right">打数</th>
                  <th class="px-4 py-3 text-right">安打</th>
                  <th class="px-4 py-3 text-right">本塁打</th>
                  <th class="px-4 py-3 text-right">累積打率</th>
                  <th class="px-4 py-3 text-right font-bold text-navy-700">累積OPS</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                <tr
                  v-for="(row, i) in trendFiltered"
                  :key="i"
                  class="hover:bg-slate-50"
                >
                  <td class="px-4 py-3 font-medium text-slate-800">{{ row.player_name }}</td>
                  <td class="px-4 py-3 text-slate-600">{{ row.game_date }}</td>
                  <td class="px-4 py-3 text-slate-600">{{ row.opponent }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ row.at_bat_count }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ row.hit_count }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ row.homerun }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ fmt(row.cum_avg) }}</td>
                  <td class="px-4 py-3 text-right font-bold text-navy-700">{{ fmt(row.cum_ops) }}</td>
                </tr>
                <tr v-if="trendFiltered.length === 0">
                  <td colspan="8" class="px-4 py-8 text-center text-slate-400">
                    選手を選択してください
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Bar, Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import { analyticsApi, playersApi, statsApi } from '../api/index.js'
import { useYear } from '../composables/useYear.js'
import YearSelector from '../components/YearSelector.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import ErrorAlert from '../components/ErrorAlert.vue'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
)

const { year } = useYear()
const loading = ref(false)
const error = ref('')
const directions = ref([])
const trend = ref([])
const playerList = ref([])
const teamRecord = ref({})
const selectedPlayerId = ref(null)
const activeTab = ref('direction')

const tabs = [
  { key: 'direction', label: '打球方向' },
  { key: 'trend',     label: '累積成績推移' },
]

const trendFiltered = computed(() =>
  selectedPlayerId.value
    ? trend.value.filter(r => r.player_id === selectedPlayerId.value)
    : [],
)

function fmt(val) {
  return val != null ? val.toFixed(3) : '—'
}

// ---- 打球方向グラフ ----
const DIRECTION_COLORS = ['#ef4444', '#f97316', '#22c55e', '#3b82f6', '#8b5cf6']

const directionChartData = computed(() => ({
  labels: directions.value.map(p => p.player_name),
  datasets: [
    { label: '右(9)',  data: directions.value.map(p => p.pct_right_9),     backgroundColor: DIRECTION_COLORS[0] },
    { label: '右中',   data: directions.value.map(p => p.pct_right_center), backgroundColor: DIRECTION_COLORS[1] },
    { label: '中',     data: directions.value.map(p => p.pct_center),       backgroundColor: DIRECTION_COLORS[2] },
    { label: '左中',   data: directions.value.map(p => p.pct_left_center),  backgroundColor: DIRECTION_COLORS[3] },
    { label: '左(7)',  data: directions.value.map(p => p.pct_left_7),       backgroundColor: DIRECTION_COLORS[4] },
  ],
}))

const directionChartOptions = {
  indexAxis: 'y',
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom' },
    tooltip: {
      callbacks: {
        label: ctx => `${ctx.dataset.label}: ${ctx.parsed.x}%`,
      },
    },
  },
  scales: {
    x: { stacked: true, max: 100, ticks: { callback: v => `${v}%` } },
    y: { stacked: true },
  },
}

// 選手数に応じてチャート高さを動的に決定
const directionChartHeight = computed(() => {
  const h = Math.max(200, directions.value.length * 40 + 60)
  return `${h}px`
})

// ---- 累積OPS推移グラフ ----
const trendChartData = computed(() => {
  const rows = trendFiltered.value
  return {
    labels: rows.map(r => r.game_date),
    datasets: [
      {
        label: '累積打率',
        data: rows.map(r => r.cum_avg),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59,130,246,0.1)',
        tension: 0.3,
        fill: false,
        pointRadius: 4,
      },
      {
        label: '累積OPS',
        data: rows.map(r => r.cum_ops),
        borderColor: '#f97316',
        backgroundColor: 'rgba(249,115,22,0.1)',
        tension: 0.3,
        fill: false,
        pointRadius: 4,
      },
    ],
  }
})

const trendChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom' },
    tooltip: {
      callbacks: {
        label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y?.toFixed(3) ?? '—'}`,
      },
    },
  },
  scales: {
    y: {
      min: 0,
      ticks: { callback: v => v.toFixed(3) },
    },
  },
}

async function fetchAll() {
  loading.value = true
  error.value = ''
  try {
    const [d, t, p, rec] = await Promise.all([
      analyticsApi.hitDirection(year.value),
      analyticsApi.battingTrend(year.value),
      playersApi.list(year.value),
      statsApi.teamRecord(year.value),
    ])
    directions.value = d
    trend.value = t
    playerList.value = p
    teamRecord.value = rec
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(fetchAll)
</script>
