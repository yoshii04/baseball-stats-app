<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-slate-800">試合一覧</h1>
      <div class="flex items-center gap-2">
        <select
          v-model="month"
          @change="fetch"
          class="border border-slate-300 rounded-md px-3 py-1.5 text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-navy-600"
        >
          <option :value="null">全月</option>
          <option v-for="m in 12" :key="m" :value="m">{{ m }}月</option>
        </select>
        <YearSelector v-model="year" @update:modelValue="fetch" />
      </div>
    </div>

    <LoadingSpinner v-if="loading" />
    <ErrorAlert v-else-if="error" :message="error" />

    <template v-else>
      <!-- チーム戦績サマリー -->
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

      <div class="bg-white rounded-lg shadow-sm border border-slate-200">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-slate-50 text-slate-500 text-xs uppercase">
              <tr>
                <th class="px-4 py-3 text-left">日付</th>
                <th class="px-4 py-3 text-center">第</th>
                <th class="px-4 py-3 text-left">対戦相手</th>
                <th class="px-4 py-3 text-center">{{ TEAM_NAME }}</th>
                <th class="px-4 py-3 text-center">相手</th>
                <th class="px-4 py-3 text-center">結果</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr
                v-for="g in games"
                :key="g.game_id"
                class="hover:bg-slate-50 transition-colors cursor-pointer"
                @click="selectGame(g)"
              >
                <td class="px-4 py-3 text-slate-700 font-medium">{{ g.game_date }}</td>
                <td class="px-4 py-3 text-center text-slate-500">{{ g.game_number }}</td>
                <td class="px-4 py-3 text-slate-600">{{ g.away_team }}</td>
                <td class="px-4 py-3 text-center text-slate-700 font-semibold">{{ g.home_score ?? '—' }}</td>
                <td class="px-4 py-3 text-center text-slate-600">{{ g.away_score ?? '—' }}</td>
                <td class="px-4 py-3 text-center">
                  <span
                    v-if="g.result"
                    :class="{
                      'text-green-600 font-bold': g.result === '〇',
                      'text-red-500 font-bold': g.result === '×',
                      'text-amber-500 font-bold': g.result === '△',
                    }"
                  >{{ g.result }}</span>
                  <span v-else class="text-slate-400">—</span>
                </td>
              </tr>
              <tr v-if="games.length === 0">
                <td colspan="6" class="px-4 py-8 text-center text-slate-400">試合データがありません</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <p class="mt-2 text-xs text-slate-400 text-right">{{ games.length }} 試合</p>

      <!-- 試合詳細モーダル -->
      <div
        v-if="selectedGame"
        class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
        @click.self="selectedGame = null"
      >
        <div class="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-y-auto">
          <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100">
            <h2 class="font-bold text-slate-800">
              {{ selectedGame.game_date }} vs {{ selectedGame.away_team }}
              <span class="text-sm font-normal text-slate-500 ml-2">第{{ selectedGame.game_number }}試合</span>
            </h2>
            <button @click="selectedGame = null" class="text-slate-400 hover:text-slate-600 text-xl">✕</button>
          </div>
          <div class="px-6 py-4">
            <LoadingSpinner v-if="detailLoading" />
            <ErrorAlert v-else-if="detailError" :message="detailError" />
            <template v-else-if="gameDetail">
              <table class="w-full text-sm">
                <thead class="bg-slate-50 text-slate-500 text-xs uppercase">
                  <tr>
                    <th class="px-3 py-2 text-left">選手名</th>
                    <th class="px-3 py-2 text-right">打数</th>
                    <th class="px-3 py-2 text-right">安打</th>
                    <th class="px-3 py-2 text-right">2塁打</th>
                    <th class="px-3 py-2 text-right">3塁打</th>
                    <th class="px-3 py-2 text-right">本塁打</th>
                    <th class="px-3 py-2 text-right">四死球</th>
                    <th class="px-3 py-2 text-right">三振</th>
                    <th class="px-3 py-2 text-right">打率</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                  <tr v-for="p in gameDetail.players" :key="p.player_id" class="hover:bg-slate-50">
                    <td class="px-3 py-2 font-medium text-slate-800">{{ p.player_name }}</td>
                    <td class="px-3 py-2 text-right text-slate-600">{{ p.at_bat_count }}</td>
                    <td class="px-3 py-2 text-right text-slate-600">{{ p.hit_count }}</td>
                    <td class="px-3 py-2 text-right text-slate-600">{{ p.double_hit }}</td>
                    <td class="px-3 py-2 text-right text-slate-600">{{ p.triple }}</td>
                    <td class="px-3 py-2 text-right text-slate-600">{{ p.homerun }}</td>
                    <td class="px-3 py-2 text-right text-slate-600">{{ p.walk_count }}</td>
                    <td class="px-3 py-2 text-right text-slate-600">{{ p.strike_out }}</td>
                    <td class="px-3 py-2 text-right text-slate-600">{{ fmt(p.batting_avg) }}</td>
                  </tr>
                </tbody>
              </table>
            </template>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { gamesApi, statsApi } from '../api/index.js'
import { useYear } from '../composables/useYear.js'
import { TEAM_NAME } from '../config.js'
import YearSelector from '../components/YearSelector.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import ErrorAlert from '../components/ErrorAlert.vue'

const { year } = useYear()
const month = ref(null)
const loading = ref(false)
const error = ref('')
const games = ref([])
const teamRecord = ref({})

const selectedGame = ref(null)
const gameDetail = ref(null)
const detailLoading = ref(false)
const detailError = ref('')

function fmt(val) {
  return val != null ? val.toFixed(3) : '—'
}

async function fetch() {
  loading.value = true
  error.value = ''
  try {
    const [gamesData, record] = await Promise.all([
      gamesApi.list(year.value, month.value),
      statsApi.teamRecord(year.value),
    ])
    games.value = gamesData
    teamRecord.value = record
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function selectGame(game) {
  selectedGame.value = game
  gameDetail.value = null
  detailLoading.value = true
  detailError.value = ''
  try {
    gameDetail.value = await gamesApi.get(game.game_id)
  } catch (e) {
    detailError.value = e.message
  } finally {
    detailLoading.value = false
  }
}

onMounted(fetch)
</script>
