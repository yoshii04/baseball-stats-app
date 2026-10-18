<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-slate-800">投手成績</h1>
      <YearSelector v-model="year" @update:modelValue="fetchData" />
    </div>

    <LoadingSpinner v-if="loading" />
    <ErrorAlert v-else-if="error" :message="error" />

    <template v-else>
      <!-- チーム投手成績サマリー -->
      <div v-if="teamPitching.game_count != null" class="mb-6 bg-slate-50 border border-slate-200 rounded-lg p-4">
        <h2 class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">チーム成績</h2>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="text-xs text-slate-400">
              <tr>
                <th class="pr-3 pb-1 text-left font-normal w-16"></th>
                <th class="pr-4 pb-1 text-right font-normal">登板</th>
                <th class="pr-4 pb-1 text-right font-normal">IP</th>
                <th class="pr-4 pb-1 text-right font-normal">対戦打者</th>
                <th class="pr-4 pb-1 text-right font-normal">投球数</th>
                <th class="pr-4 pb-1 text-right font-normal">被安打</th>
                <th class="pr-4 pb-1 text-right font-normal">被本塁打</th>
                <th class="pr-4 pb-1 text-right font-normal">与四死球</th>
                <th class="pr-4 pb-1 text-right font-normal">奪三振</th>
                <th class="pr-4 pb-1 text-right font-normal">失点</th>
                <th class="pr-4 pb-1 text-right font-normal">自責点</th>
                <th class="pr-4 pb-1 text-right font-normal">WHIP</th>
                <th class="pb-1 text-right font-bold text-blue-700">防御率</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr class="font-semibold text-slate-700">
                <td class="pr-3 text-left text-xs text-slate-400">合計</td>
                <td class="pr-4 text-right">{{ teamPitching.game_count }}</td>
                <td class="pr-4 text-right">{{ teamPitching.ip }}</td>
                <td class="pr-4 text-right">{{ teamPitching.batters_faced }}</td>
                <td class="pr-4 text-right">{{ teamPitching.pitch_count }}</td>
                <td class="pr-4 text-right">{{ teamPitching.hits_allowed }}</td>
                <td class="pr-4 text-right">{{ teamPitching.homerun_allowed }}</td>
                <td class="pr-4 text-right">{{ teamPitching.walks_allowed }}</td>
                <td class="pr-4 text-right">{{ teamPitching.strikeouts }}</td>
                <td class="pr-4 text-right">{{ teamPitching.runs_allowed }}</td>
                <td class="pr-4 text-right">{{ teamPitching.earned_runs }}</td>
                <td class="pr-4 text-right">{{ fmtWhip(teamPitching.whip) }}</td>
                <td class="text-right font-bold text-blue-700">{{ fmtEra(teamPitching.era) }}</td>
              </tr>
              <tr
                v-for="gn in (teamPitching.by_game_number || [])"
                :key="gn.game_number"
                class="text-slate-600"
              >
                <td class="pr-3 text-left text-xs font-semibold text-slate-400">第{{ gn.game_number }}試合</td>
                <td class="pr-4 text-right">{{ gn.game_count }}</td>
                <td class="pr-4 text-right">{{ gn.ip }}</td>
                <td class="pr-4 text-right">{{ gn.batters_faced }}</td>
                <td class="pr-4 text-right">{{ gn.pitch_count }}</td>
                <td class="pr-4 text-right">{{ gn.hits_allowed }}</td>
                <td class="pr-4 text-right">{{ gn.homerun_allowed }}</td>
                <td class="pr-4 text-right">{{ gn.walks_allowed }}</td>
                <td class="pr-4 text-right">{{ gn.strikeouts }}</td>
                <td class="pr-4 text-right">{{ gn.runs_allowed }}</td>
                <td class="pr-4 text-right">{{ gn.earned_runs }}</td>
                <td class="pr-4 text-right">{{ fmtWhip(gn.whip) }}</td>
                <td class="text-right font-bold text-blue-700">{{ fmtEra(gn.era) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 規定投球回数の表示 -->
      <p class="mb-3 text-sm text-slate-500">
        規定投球回数：{{ qualifyingInnings }} 回
        <span class="text-slate-400 ml-1">（チーム試合数 {{ totalGames }} × 1回）</span>
      </p>

      <!-- 規定投球回数到達者 -->
      <section class="mb-6">
        <h2 class="text-sm font-semibold text-slate-600 uppercase tracking-wide mb-2">
          規定投球回数到達
          <span class="text-slate-400 font-normal ml-1">（{{ qualified.length }} 名）</span>
        </h2>
        <PitcherTable :pitchers="qualified" @select="selectPitcher" />
      </section>

      <!-- 規定投球回数未到達者 -->
      <section>
        <h2 class="text-sm font-semibold text-slate-400 uppercase tracking-wide mb-2">
          規定投球回数未到達
          <span class="font-normal ml-1">（{{ unqualified.length }} 名）</span>
        </h2>
        <PitcherTable :pitchers="unqualified" :dimmed="true" @select="selectPitcher" />
      </section>

      <!-- 試合別成績モーダル -->
      <div
        v-if="selectedPitcher"
        class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
        @click.self="selectedPitcher = null"
      >
        <div class="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[80vh] overflow-y-auto">
          <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100">
            <h2 class="font-bold text-slate-800">
              {{ selectedPitcher.player_name }} 試合別成績
              <span class="text-sm font-normal text-slate-500 ml-2">{{ year != null ? `${year}年` : '通算' }}</span>
            </h2>
            <button @click="selectedPitcher = null" class="text-slate-400 hover:text-slate-600 text-xl">✕</button>
          </div>
          <div class="px-6 py-4">
            <LoadingSpinner v-if="detailLoading" />
            <ErrorAlert v-else-if="detailError" :message="detailError" />
            <template v-else-if="pitcherStats.length > 0">
              <table class="w-full text-sm">
                <thead class="bg-slate-50 text-slate-500 text-xs uppercase">
                  <tr>
                    <th class="px-3 py-2 text-left">日付</th>
                    <th class="px-3 py-2 text-left">対戦相手</th>
                    <th class="px-3 py-2 text-right">第</th>
                    <th class="px-3 py-2 text-right">IP</th>
                    <th class="px-3 py-2 text-right">対戦</th>
                    <th class="px-3 py-2 text-right">投球</th>
                    <th class="px-3 py-2 text-right">被安打</th>
                    <th class="px-3 py-2 text-right">与四死球</th>
                    <th class="px-3 py-2 text-right">奪三振</th>
                    <th class="px-3 py-2 text-right">失点</th>
                    <th class="px-3 py-2 text-right">自責点</th>
                    <th class="px-3 py-2 text-right font-bold">防御率</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                  <tr v-for="s in pitcherStats" :key="s.game_id" class="hover:bg-slate-50">
                    <td class="px-3 py-2 text-slate-700">{{ s.game_date }}</td>
                    <td class="px-3 py-2 text-slate-600">{{ s.opponent }}</td>
                    <td class="px-3 py-2 text-right text-slate-500">{{ s.game_number }}</td>
                    <td class="px-3 py-2 text-right text-slate-600">{{ s.ip }}</td>
                    <td class="px-3 py-2 text-right text-slate-600">{{ s.batters_faced }}</td>
                    <td class="px-3 py-2 text-right text-slate-600">{{ s.pitch_count }}</td>
                    <td class="px-3 py-2 text-right text-slate-600">{{ s.hits_allowed }}</td>
                    <td class="px-3 py-2 text-right text-slate-600">{{ s.walks_allowed }}</td>
                    <td class="px-3 py-2 text-right text-slate-600">{{ s.strikeouts }}</td>
                    <td class="px-3 py-2 text-right text-slate-600">{{ s.runs_allowed }}</td>
                    <td class="px-3 py-2 text-right text-slate-600">{{ s.earned_runs }}</td>
                    <td class="px-3 py-2 text-right font-bold text-slate-700">{{ fmtEra(s.era) }}</td>
                  </tr>
                </tbody>
              </table>
            </template>
            <p v-else class="text-center text-slate-400 py-4">データがありません</p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, defineComponent, h } from 'vue'
import { pitchersApi, statsApi } from '../api/index.js'
import { useYear } from '../composables/useYear.js'
import YearSelector from '../components/YearSelector.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import ErrorAlert from '../components/ErrorAlert.vue'

const { year } = useYear()
const loading = ref(false)
const error = ref('')
const pitchers = ref([])
const totalGames = ref(0)
const qualifyingInnings = ref(0)
const teamPitching = ref({})

const qualified = computed(() => pitchers.value.filter(p => p.qualified))
const unqualified = computed(() => pitchers.value.filter(p => !p.qualified))

const selectedPitcher = ref(null)
const pitcherStats = ref([])
const detailLoading = ref(false)
const detailError = ref('')

function fmtEra(val) {
  return val != null ? val.toFixed(2) : '—'
}
function fmtWhip(val) {
  return val != null ? val.toFixed(2) : '—'
}

async function fetchData() {
  loading.value = true
  error.value = ''
  try {
    const [data, tp] = await Promise.all([
      pitchersApi.list(year.value),
      statsApi.teamPitching(year.value),
    ])
    pitchers.value = data.pitchers
    totalGames.value = data.total_games
    qualifyingInnings.value = data.qualifying_innings
    teamPitching.value = tp
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function selectPitcher(pitcher) {
  selectedPitcher.value = pitcher
  pitcherStats.value = []
  detailLoading.value = true
  detailError.value = ''
  try {
    pitcherStats.value = await pitchersApi.stats(pitcher.player_id, year.value)
  } catch (e) {
    detailError.value = e.message
  } finally {
    detailLoading.value = false
  }
}

// ---------- 投手テーブルコンポーネント（インライン定義） ----------
const PitcherTable = defineComponent({
  props: {
    pitchers: { type: Array, default: () => [] },
    dimmed:   { type: Boolean, default: false },
  },
  emits: ['select'],
  setup(props, { emit }) {
    return () => h('div', { class: 'bg-white rounded-lg shadow-sm border border-slate-200' }, [
      h('div', { class: 'overflow-x-auto' }, [
        h('table', { class: 'w-full text-sm' }, [
          h('thead', { class: 'bg-slate-50 text-slate-500 text-xs uppercase' }, [
            h('tr', {}, [
              h('th', { class: 'px-4 py-3 text-left' }, '投手名'),
              h('th', { class: 'px-4 py-3 text-right' }, '登板'),
              h('th', { class: 'px-4 py-3 text-right' }, 'IP'),
              h('th', { class: 'px-4 py-3 text-right' }, '対戦打者'),
              h('th', { class: 'px-4 py-3 text-right' }, '投球数'),
              h('th', { class: 'px-4 py-3 text-right' }, '被安打'),
              h('th', { class: 'px-4 py-3 text-right' }, '被本塁打'),
              h('th', { class: 'px-4 py-3 text-right' }, '与四死球'),
              h('th', { class: 'px-4 py-3 text-right' }, '奪三振'),
              h('th', { class: 'px-4 py-3 text-right' }, '失点'),
              h('th', { class: 'px-4 py-3 text-right' }, '自責点'),
              h('th', { class: 'px-4 py-3 text-right' }, 'WHIP'),
              h('th', { class: 'px-4 py-3 text-right font-bold text-blue-700' }, '防御率'),
            ]),
          ]),
          h('tbody', { class: 'divide-y divide-slate-100' }, [
            ...(props.pitchers.length === 0
              ? [h('tr', {}, [h('td', { colspan: 13, class: 'px-4 py-8 text-center text-slate-400' }, 'データがありません')])]
              : props.pitchers.map(p =>
                  h('tr', {
                    key: p.player_id,
                    class: `transition-colors cursor-pointer ${props.dimmed ? 'text-slate-400 hover:bg-slate-50' : 'hover:bg-slate-50'}`,
                    onClick: () => emit('select', p),
                  }, [
                    h('td', { class: `px-4 py-3 font-medium ${props.dimmed ? 'text-slate-400' : 'text-navy-700'}` }, p.player_name),
                    h('td', { class: 'px-4 py-3 text-right' }, p.game_count),
                    h('td', { class: 'px-4 py-3 text-right' }, p.ip),
                    h('td', { class: 'px-4 py-3 text-right' }, p.batters_faced),
                    h('td', { class: 'px-4 py-3 text-right' }, p.pitch_count),
                    h('td', { class: 'px-4 py-3 text-right' }, p.hits_allowed),
                    h('td', { class: 'px-4 py-3 text-right' }, p.homerun_allowed),
                    h('td', { class: 'px-4 py-3 text-right' }, p.walks_allowed),
                    h('td', { class: 'px-4 py-3 text-right' }, p.strikeouts),
                    h('td', { class: 'px-4 py-3 text-right' }, p.runs_allowed),
                    h('td', { class: 'px-4 py-3 text-right' }, p.earned_runs),
                    h('td', { class: 'px-4 py-3 text-right' }, fmtWhip(p.whip)),
                    h('td', { class: `px-4 py-3 text-right font-bold ${props.dimmed ? 'text-slate-400' : 'text-blue-700'}` }, fmtEra(p.era)),
                  ])
                )
            ),
          ]),
        ]),
      ]),
    ])
  },
})

onMounted(fetchData)
</script>
