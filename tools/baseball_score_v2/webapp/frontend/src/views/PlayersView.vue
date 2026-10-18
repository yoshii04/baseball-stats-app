<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-slate-800">打撃成績</h1>
      <YearSelector v-model="year" @update:modelValue="fetch" />
    </div>

    <LoadingSpinner v-if="loading" />
    <ErrorAlert v-else-if="error" :message="error" />

    <template v-else>
      <!-- チーム打撃成績サマリー -->
      <div v-if="teamBatting.game_count != null" class="mb-6 bg-slate-50 border border-slate-200 rounded-lg p-4">
        <h2 class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">チーム成績</h2>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="text-xs text-slate-400">
              <tr>
                <th class="pr-3 pb-1 text-left font-normal w-16"></th>
                <th class="pr-4 pb-1 text-right font-normal">試合</th>
                <th class="pr-4 pb-1 text-right font-normal">打席</th>
                <th class="pr-4 pb-1 text-right font-normal">打数</th>
                <th class="pr-4 pb-1 text-right font-normal">安打</th>
                <th class="pr-4 pb-1 text-right font-normal">1塁打</th>
                <th class="pr-4 pb-1 text-right font-normal">2塁打</th>
                <th class="pr-4 pb-1 text-right font-normal">3塁打</th>
                <th class="pr-4 pb-1 text-right font-normal">本塁打</th>
                <th class="pr-4 pb-1 text-right font-normal">四死球</th>
                <th class="pr-4 pb-1 text-right font-normal">三振</th>
                <th class="pr-4 pb-1 text-right font-normal">盗塁</th>
                <th class="pr-4 pb-1 text-right font-normal">打率</th>
                <th class="pr-4 pb-1 text-right font-normal">出塁率</th>
                <th class="pr-4 pb-1 text-right font-normal">長打率</th>
                <th class="pb-1 text-right font-bold text-navy-700">OPS</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr class="font-semibold text-slate-700">
                <td class="pr-3 text-left text-xs text-slate-400">合計</td>
                <td class="pr-4 text-right">{{ teamBatting.game_count }}</td>
                <td class="pr-4 text-right">{{ teamBatting.plate_appearance }}</td>
                <td class="pr-4 text-right">{{ teamBatting.at_bat_count }}</td>
                <td class="pr-4 text-right">{{ teamBatting.hit_count }}</td>
                <td class="pr-4 text-right">{{ teamBatting.single }}</td>
                <td class="pr-4 text-right">{{ teamBatting.double_hit }}</td>
                <td class="pr-4 text-right">{{ teamBatting.triple }}</td>
                <td class="pr-4 text-right">{{ teamBatting.homerun }}</td>
                <td class="pr-4 text-right">{{ teamBatting.walk_count }}</td>
                <td class="pr-4 text-right">{{ teamBatting.strike_out }}</td>
                <td class="pr-4 text-right">{{ teamBatting.stolen_base }}</td>
                <td class="pr-4 text-right">{{ fmt(teamBatting.batting_avg) }}</td>
                <td class="pr-4 text-right">{{ fmt(teamBatting.on_base_pct) }}</td>
                <td class="pr-4 text-right">{{ fmt(teamBatting.slg) }}</td>
                <td class="text-right font-bold text-navy-700">{{ fmt(teamBatting.ops) }}</td>
              </tr>
              <tr
                v-for="gn in (teamBatting.by_game_number || [])"
                :key="gn.game_number"
                class="text-slate-600"
              >
                <td class="pr-3 text-left text-xs font-semibold text-slate-400">第{{ gn.game_number }}試合</td>
                <td class="pr-4 text-right">{{ gn.game_count }}</td>
                <td class="pr-4 text-right">{{ gn.plate_appearance }}</td>
                <td class="pr-4 text-right">{{ gn.at_bat_count }}</td>
                <td class="pr-4 text-right">{{ gn.hit_count }}</td>
                <td class="pr-4 text-right">{{ gn.single }}</td>
                <td class="pr-4 text-right">{{ gn.double_hit }}</td>
                <td class="pr-4 text-right">{{ gn.triple }}</td>
                <td class="pr-4 text-right">{{ gn.homerun }}</td>
                <td class="pr-4 text-right">{{ gn.walk_count }}</td>
                <td class="pr-4 text-right">{{ gn.strike_out }}</td>
                <td class="pr-4 text-right">{{ gn.stolen_base }}</td>
                <td class="pr-4 text-right">{{ fmt(gn.batting_avg) }}</td>
                <td class="pr-4 text-right">{{ fmt(gn.on_base_pct) }}</td>
                <td class="pr-4 text-right">{{ fmt(gn.slg) }}</td>
                <td class="text-right font-bold text-navy-700">{{ fmt(gn.ops) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 検索ボックス -->
      <div class="mb-4">
        <input
          v-model="search"
          type="text"
          placeholder="選手名で絞り込み..."
          class="w-64 border border-slate-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-navy-600"
        />
      </div>

      <!-- 規定打席到達者 -->
      <div class="mb-8">
        <h2 class="text-base font-semibold text-slate-700 mb-2">
          規定打席到達者
          <span class="text-xs font-normal text-slate-400 ml-1">（規定: {{ qualifyThreshold.toFixed(1) }} 打席以上）</span>
        </h2>
        <div class="bg-white rounded-lg shadow-sm border border-slate-200">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="bg-slate-50 text-slate-500 text-xs uppercase">
                <tr>
                  <th class="px-4 py-3 text-left cursor-pointer select-none hover:text-slate-700" @click="sortBy('player_name')">
                    選手名{{ sortIndicator('player_name') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-700" @click="sortBy('game_count')">
                    試合{{ sortIndicator('game_count') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-700" @click="sortBy('plate_appearance')">
                    打席{{ sortIndicator('plate_appearance') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-700" @click="sortBy('at_bat_count')">
                    打数{{ sortIndicator('at_bat_count') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-700" @click="sortBy('hit_count')">
                    安打{{ sortIndicator('hit_count') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-700" @click="sortBy('single')">
                    1塁打{{ sortIndicator('single') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-700" @click="sortBy('double_hit')">
                    2塁打{{ sortIndicator('double_hit') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-700" @click="sortBy('triple')">
                    3塁打{{ sortIndicator('triple') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-700" @click="sortBy('homerun')">
                    本塁打{{ sortIndicator('homerun') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-700" @click="sortBy('walk_count')">
                    四死球{{ sortIndicator('walk_count') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-700" @click="sortBy('strike_out')">
                    三振{{ sortIndicator('strike_out') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-700" @click="sortBy('stolen_base')">
                    盗塁{{ sortIndicator('stolen_base') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-700" @click="sortBy('batting_avg')">
                    打率{{ sortIndicator('batting_avg') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-700" @click="sortBy('on_base_pct')">
                    出塁率{{ sortIndicator('on_base_pct') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-700" @click="sortBy('slg')">
                    長打率{{ sortIndicator('slg') }}
                  </th>
                  <th class="px-4 py-3 text-right font-bold text-navy-700 cursor-pointer select-none hover:text-navy-900" @click="sortBy('ops')">
                    OPS{{ sortIndicator('ops') }}
                  </th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                <tr
                  v-for="p in qualified"
                  :key="p.player_id"
                  class="hover:bg-slate-50 transition-colors cursor-pointer"
                  @click="$router.push({ name: 'playerDetail', params: { id: p.player_id } })"
                >
                  <td class="px-4 py-3 font-medium text-navy-700 hover:underline">{{ p.player_name }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ p.game_count }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ p.plate_appearance }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ p.at_bat_count }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ p.hit_count }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ p.single }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ p.double_hit }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ p.triple }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ p.homerun }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ p.walk_count }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ p.strike_out }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ p.stolen_base }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ fmt(p.batting_avg) }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ fmt(p.on_base_pct) }}</td>
                  <td class="px-4 py-3 text-right text-slate-600">{{ fmt(p.slg) }}</td>
                  <td class="px-4 py-3 text-right font-bold text-navy-700">{{ fmt(p.ops) }}</td>
                </tr>
                <tr v-if="qualified.length === 0">
                  <td colspan="16" class="px-4 py-6 text-center text-slate-400">
                    規定打席到達者はいません
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <p class="mt-1 text-xs text-slate-400 text-right">{{ qualified.length }} 名</p>
      </div>

      <!-- 規定打席未到達者 -->
      <div>
        <h2 class="text-base font-semibold text-slate-500 mb-2">規定打席未到達者</h2>
        <div class="bg-white rounded-lg shadow-sm border border-slate-200 opacity-80">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="bg-slate-50 text-slate-400 text-xs uppercase">
                <tr>
                  <th class="px-4 py-3 text-left cursor-pointer select-none hover:text-slate-600" @click="sortBy('player_name')">
                    選手名{{ sortIndicator('player_name') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-600" @click="sortBy('game_count')">
                    試合{{ sortIndicator('game_count') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-600" @click="sortBy('plate_appearance')">
                    打席{{ sortIndicator('plate_appearance') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-600" @click="sortBy('at_bat_count')">
                    打数{{ sortIndicator('at_bat_count') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-600" @click="sortBy('hit_count')">
                    安打{{ sortIndicator('hit_count') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-600" @click="sortBy('single')">
                    1塁打{{ sortIndicator('single') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-600" @click="sortBy('double_hit')">
                    2塁打{{ sortIndicator('double_hit') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-600" @click="sortBy('triple')">
                    3塁打{{ sortIndicator('triple') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-600" @click="sortBy('homerun')">
                    本塁打{{ sortIndicator('homerun') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-600" @click="sortBy('walk_count')">
                    四死球{{ sortIndicator('walk_count') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-600" @click="sortBy('strike_out')">
                    三振{{ sortIndicator('strike_out') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-600" @click="sortBy('stolen_base')">
                    盗塁{{ sortIndicator('stolen_base') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-600" @click="sortBy('batting_avg')">
                    打率{{ sortIndicator('batting_avg') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-600" @click="sortBy('on_base_pct')">
                    出塁率{{ sortIndicator('on_base_pct') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-600" @click="sortBy('slg')">
                    長打率{{ sortIndicator('slg') }}
                  </th>
                  <th class="px-4 py-3 text-right cursor-pointer select-none hover:text-slate-600" @click="sortBy('ops')">
                    OPS{{ sortIndicator('ops') }}
                  </th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                <tr
                  v-for="p in notQualified"
                  :key="p.player_id"
                  class="hover:bg-slate-50 transition-colors cursor-pointer"
                  @click="$router.push({ name: 'playerDetail', params: { id: p.player_id } })"
                >
                  <td class="px-4 py-3 font-medium text-slate-600 hover:underline">{{ p.player_name }}</td>
                  <td class="px-4 py-3 text-right text-slate-500">{{ p.game_count }}</td>
                  <td class="px-4 py-3 text-right text-slate-500">{{ p.plate_appearance }}</td>
                  <td class="px-4 py-3 text-right text-slate-500">{{ p.at_bat_count }}</td>
                  <td class="px-4 py-3 text-right text-slate-500">{{ p.hit_count }}</td>
                  <td class="px-4 py-3 text-right text-slate-500">{{ p.single }}</td>
                  <td class="px-4 py-3 text-right text-slate-500">{{ p.double_hit }}</td>
                  <td class="px-4 py-3 text-right text-slate-500">{{ p.triple }}</td>
                  <td class="px-4 py-3 text-right text-slate-500">{{ p.homerun }}</td>
                  <td class="px-4 py-3 text-right text-slate-500">{{ p.walk_count }}</td>
                  <td class="px-4 py-3 text-right text-slate-500">{{ p.strike_out }}</td>
                  <td class="px-4 py-3 text-right text-slate-500">{{ p.stolen_base }}</td>
                  <td class="px-4 py-3 text-right text-slate-500">{{ fmt(p.batting_avg) }}</td>
                  <td class="px-4 py-3 text-right text-slate-500">{{ fmt(p.on_base_pct) }}</td>
                  <td class="px-4 py-3 text-right text-slate-500">{{ fmt(p.slg) }}</td>
                  <td class="px-4 py-3 text-right text-slate-500">{{ fmt(p.ops) }}</td>
                </tr>
                <tr v-if="notQualified.length === 0">
                  <td colspan="16" class="px-4 py-6 text-center text-slate-400">
                    該当する選手が見つかりません
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <p class="mt-1 text-xs text-slate-400 text-right">{{ notQualified.length }} 名</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { playersApi, statsApi } from '../api/index.js'
import { useYear } from '../composables/useYear.js'
import YearSelector from '../components/YearSelector.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import ErrorAlert from '../components/ErrorAlert.vue'

const { year } = useYear()
const loading = ref(false)
const error = ref('')
const players = ref([])
const teamBatting = ref({})
const search = ref('')
const sortKey = ref('ops')
const sortDir = ref(-1) // -1: 降順, 1: 昇順

// チームの総試合数（最大出場試合数で代替）
const totalGames = computed(() =>
  players.value.length ? Math.max(...players.value.map(p => p.game_count)) : 0,
)

// 規定打席 = 総試合数 × 1.1
const qualifyThreshold = computed(() => totalGames.value * 1.1)

function sortBy(key) {
  if (sortKey.value === key) {
    sortDir.value *= -1
  } else {
    sortKey.value = key
    // 名前は昇順デフォルト、数値系は降順デフォルト
    sortDir.value = key === 'player_name' ? 1 : -1
  }
}

function sortIndicator(key) {
  if (sortKey.value !== key) return ''
  return sortDir.value === -1 ? ' ▼' : ' ▲'
}

function fmt(val) {
  return val != null ? val.toFixed(3) : '—'
}

function compareVal(a, b, key) {
  const av = a[key] ?? (key === 'player_name' ? '' : -Infinity)
  const bv = b[key] ?? (key === 'player_name' ? '' : -Infinity)
  if (av < bv) return -1
  if (av > bv) return 1
  return 0
}

const sorted = computed(() => {
  const list = search.value
    ? players.value.filter(p => p.player_name.includes(search.value))
    : [...players.value]
  return list.sort((a, b) => compareVal(a, b, sortKey.value) * sortDir.value)
})

const qualified = computed(() =>
  sorted.value.filter(p => p.plate_appearance >= qualifyThreshold.value),
)

const notQualified = computed(() =>
  sorted.value.filter(p => p.plate_appearance < qualifyThreshold.value),
)

async function fetch() {
  loading.value = true
  error.value = ''
  try {
    [players.value, teamBatting.value] = await Promise.all([
      playersApi.list(year.value),
      statsApi.teamBatting(year.value),
    ])
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(fetch)
</script>
