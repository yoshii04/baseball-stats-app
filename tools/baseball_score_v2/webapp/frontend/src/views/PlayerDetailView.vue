<template>
  <div>
    <!-- ヘッダー -->
    <div class="flex flex-wrap items-center gap-3 mb-6">
      <RouterLink
        to="/players"
        class="text-sm text-slate-500 hover:text-slate-700 flex items-center gap-1"
      >
        ← 選手一覧
      </RouterLink>
      <h1 class="text-2xl font-bold text-slate-800">{{ player?.player_name ?? '...' }}</h1>
      <span v-if="player" class="text-sm text-slate-500 bg-slate-100 rounded px-2 py-0.5">
        {{ player.team_name }}
      </span>
      <div class="ml-auto">
        <YearSelector v-model="year" @update:modelValue="fetchAll" />
      </div>
    </div>

    <LoadingSpinner v-if="loading" />
    <ErrorAlert v-else-if="error" :message="error" />

    <template v-else>
      <!-- シーズンサマリーカード -->
      <div class="grid grid-cols-3 sm:grid-cols-6 gap-3 mb-6">
        <div
          v-for="card in summaryCards"
          :key="card.label"
          class="bg-white rounded-lg shadow-sm border border-slate-200 p-4 text-center"
        >
          <div class="text-xs text-slate-500 uppercase mb-1">{{ card.label }}</div>
          <div class="text-xl font-bold" :class="card.highlight ? 'text-navy-700' : 'text-slate-800'">
            {{ card.value }}
          </div>
        </div>
      </div>

      <!-- 累積打率・OPS推移グラフ -->
      <div v-if="stats.length > 0" class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-6">
        <h2 class="font-semibold text-slate-700 mb-4">累積打率・OPS推移</h2>
        <div style="height: 260px;">
          <Line :data="trendChartData" :options="trendChartOptions" />
        </div>
      </div>

      <!-- 打球方向グラフ -->
      <div v-if="direction" class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-6">
        <h2 class="font-semibold text-slate-700 mb-4">打球方向（{{ direction.total }} 本）</h2>
        <div style="height: 120px;">
          <Bar :data="directionChartData" :options="directionChartOptions" />
        </div>
      </div>

      <!-- 試合別成績テーブル -->
      <div class="bg-white rounded-lg shadow-sm border border-slate-200">
        <div class="px-6 py-4 border-b border-slate-100">
          <h2 class="font-semibold text-slate-700">試合別成績</h2>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-slate-50 text-slate-500 text-xs uppercase">
              <tr>
                <th class="px-4 py-3 text-left">試合日</th>
                <th class="px-4 py-3 text-left">対戦相手</th>
                <th class="px-4 py-3 text-right">打数</th>
                <th class="px-4 py-3 text-right">安打</th>
                <th class="px-4 py-3 text-right">2塁打</th>
                <th class="px-4 py-3 text-right">3塁打</th>
                <th class="px-4 py-3 text-right">本塁打</th>
                <th class="px-4 py-3 text-right">打点</th>
                <th class="px-4 py-3 text-right">四死球</th>
                <th class="px-4 py-3 text-right">三振</th>
                <th class="px-4 py-3 text-right">盗塁</th>
                <th class="px-4 py-3 text-right">累積打率</th>
                <th class="px-4 py-3 text-right font-bold text-navy-700">累積OPS</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr
                v-for="(row, i) in stats"
                :key="i"
                class="hover:bg-slate-50"
              >
                <td class="px-4 py-3 text-slate-600">{{ row.game_date }}</td>
                <td class="px-4 py-3 text-slate-600">{{ row.opponent }}</td>
                <td class="px-4 py-3 text-right text-slate-600">{{ row.at_bat_count }}</td>
                <td class="px-4 py-3 text-right text-slate-600">{{ row.hit_count }}</td>
                <td class="px-4 py-3 text-right text-slate-600">{{ row.double_hit }}</td>
                <td class="px-4 py-3 text-right text-slate-600">{{ row.triple }}</td>
                <td class="px-4 py-3 text-right text-slate-600">{{ row.homerun }}</td>
                <td class="px-4 py-3 text-right text-slate-600">{{ row.rbi }}</td>
                <td class="px-4 py-3 text-right text-slate-600">{{ row.walk_count }}</td>
                <td class="px-4 py-3 text-right text-slate-600">{{ row.strike_out }}</td>
                <td class="px-4 py-3 text-right text-slate-600">{{ row.stolen_base }}</td>
                <td class="px-4 py-3 text-right text-slate-600">{{ fmt(row.cum_avg) }}</td>
                <td class="px-4 py-3 text-right font-bold text-navy-700">{{ fmt(row.cum_ops) }}</td>
              </tr>
              <tr v-if="stats.length === 0">
                <td colspan="13" class="px-4 py-8 text-center text-slate-400">
                  {{ year }}年の試合データがありません
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
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
import { playersApi, analyticsApi } from '../api/index.js'
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

const route = useRoute()
const playerId = Number(route.params.id)
const { year } = useYear()

const loading = ref(false)
const error = ref('')
const player = ref(null)
const stats = ref([])
const direction = ref(null)

// ---------- シーズンサマリー計算 ----------
const seasonSummary = computed(() => {
  if (!stats.value.length) return {}
  const s = stats.value.reduce(
    (acc, r) => ({
      game_count:   acc.game_count + 1,
      at_bat_count: acc.at_bat_count + r.at_bat_count,
      hit_count:    acc.hit_count   + r.hit_count,
      double_hit:   acc.double_hit  + r.double_hit,
      triple:       acc.triple      + r.triple,
      homerun:      acc.homerun     + r.homerun,
      rbi:          acc.rbi         + r.rbi,
      walk_count:   acc.walk_count  + r.walk_count,
      strike_out:   acc.strike_out  + r.strike_out,
      stolen_base:  acc.stolen_base + r.stolen_base,
    }),
    {
      game_count: 0, at_bat_count: 0, hit_count: 0, double_hit: 0, triple: 0,
      homerun: 0, rbi: 0, walk_count: 0, strike_out: 0, stolen_base: 0,
    },
  )
  const last = stats.value[stats.value.length - 1]
  s.batting_avg = last.cum_avg
  s.ops = last.cum_ops
  return s
})

const summaryCards = computed(() => {
  const s = seasonSummary.value
  return [
    { label: '試合',   value: s.game_count   ?? '—' },
    { label: '打数',   value: s.at_bat_count ?? '—' },
    { label: '安打',   value: s.hit_count    ?? '—' },
    { label: '本塁打', value: s.homerun       ?? '—' },
    { label: '打率',   value: fmt(s.batting_avg) },
    { label: 'OPS',    value: fmt(s.ops), highlight: true },
  ]
})

// ---------- 累積推移グラフ ----------
const trendChartData = computed(() => ({
  labels: stats.value.map(r => r.game_date),
  datasets: [
    {
      label: '累積打率',
      data: stats.value.map(r => r.cum_avg),
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59,130,246,0.1)',
      tension: 0.3,
      fill: false,
      pointRadius: 4,
    },
    {
      label: '累積OPS',
      data: stats.value.map(r => r.cum_ops),
      borderColor: '#f97316',
      backgroundColor: 'rgba(249,115,22,0.1)',
      tension: 0.3,
      fill: false,
      pointRadius: 4,
    },
  ],
}))

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

// ---------- 打球方向グラフ ----------
const DIRECTION_COLORS = ['#ef4444', '#f97316', '#22c55e', '#3b82f6', '#8b5cf6']

const directionChartData = computed(() => {
  const d = direction.value
  if (!d) return { labels: [], datasets: [] }
  return {
    labels: ['打球方向'],
    datasets: [
      { label: '右(9)',  data: [d.pct_right_9],     backgroundColor: DIRECTION_COLORS[0] },
      { label: '右中',   data: [d.pct_right_center], backgroundColor: DIRECTION_COLORS[1] },
      { label: '中',     data: [d.pct_center],       backgroundColor: DIRECTION_COLORS[2] },
      { label: '左中',   data: [d.pct_left_center],  backgroundColor: DIRECTION_COLORS[3] },
      { label: '左(7)',  data: [d.pct_left_7],       backgroundColor: DIRECTION_COLORS[4] },
    ],
  }
})

const directionChartOptions = {
  indexAxis: 'y',
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'right' },
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

// ---------- ユーティリティ ----------
function fmt(val) {
  return val != null ? val.toFixed(3) : '—'
}

// ---------- データ取得 ----------
async function fetchAll() {
  loading.value = true
  error.value = ''
  try {
    const [p, s, d] = await Promise.all([
      playersApi.get(playerId),
      playersApi.stats(playerId, year.value),
      analyticsApi.hitDirection(year.value, playerId),
    ])
    player.value = p
    stats.value = s
    direction.value = d.length > 0 ? d[0] : null
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(fetchAll)
</script>
