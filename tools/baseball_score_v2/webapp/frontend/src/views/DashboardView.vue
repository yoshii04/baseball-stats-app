<template>
  <div>
    <!-- ヘッダー -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-slate-800">ダッシュボード</h1>
      <YearSelector v-model="year" @update:modelValue="fetchAll" />
    </div>

    <LoadingSpinner v-if="loading" />
    <ErrorAlert v-else-if="error" :message="error" />

    <template v-else>
      <!-- 試合成績 -->
      <section class="mb-8">
        <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3 pl-1">試合成績</h2>
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <!-- 勝敗 メイン -->
          <div class="grid grid-cols-3 divide-x divide-slate-100">
            <div class="py-7 text-center bg-green-50">
              <p class="text-xs font-semibold text-green-600 uppercase tracking-widest mb-2">勝</p>
              <p class="text-5xl font-black text-green-600">{{ teamRecord.wins ?? '—' }}</p>
            </div>
            <div class="py-7 text-center">
              <p class="text-xs font-semibold text-red-400 uppercase tracking-widest mb-2">負</p>
              <p class="text-5xl font-black text-red-400">{{ teamRecord.losses ?? '—' }}</p>
            </div>
            <div class="py-7 text-center">
              <p class="text-xs font-semibold text-amber-400 uppercase tracking-widest mb-2">分</p>
              <p class="text-5xl font-black text-amber-400">{{ teamRecord.draws ?? '—' }}</p>
            </div>
          </div>
          <!-- サブ行 -->
          <div class="grid grid-cols-3 divide-x divide-slate-100 border-t border-slate-100 bg-slate-50">
            <div class="py-3 text-center">
              <p class="text-xs text-slate-400 mb-0.5">試合</p>
              <p class="text-lg font-bold text-slate-600">{{ teamRecord.game_count ?? '—' }}</p>
            </div>
            <div class="py-3 text-center">
              <p class="text-xs text-slate-400 mb-0.5">得点</p>
              <p class="text-lg font-bold text-slate-600">{{ teamRecord.runs_scored ?? '—' }}</p>
            </div>
            <div class="py-3 text-center">
              <p class="text-xs text-slate-400 mb-0.5">失点</p>
              <p class="text-lg font-bold text-slate-500">{{ teamRecord.runs_allowed ?? '—' }}</p>
            </div>
          </div>
          <!-- 試合別成績 -->
          <div
            v-if="teamRecord.by_game_number && teamRecord.by_game_number.length > 1"
            class="border-t border-slate-100"
          >
            <div
              v-for="gn in teamRecord.by_game_number"
              :key="gn.game_number"
              class="flex items-center gap-4 px-4 py-2 text-sm border-b border-slate-50 last:border-b-0"
            >
              <span class="text-xs font-semibold text-slate-400 w-16 shrink-0">第{{ gn.game_number }}試合</span>
              <span class="font-bold text-green-600">○{{ gn.wins }}</span>
              <span class="font-bold text-red-400">×{{ gn.losses }}</span>
              <span class="font-bold text-amber-400">△{{ gn.draws }}</span>
              <span class="text-slate-400 mx-1">|</span>
              <span class="text-slate-500 text-xs">{{ gn.game_count }}試合</span>
              <span class="text-slate-400 text-xs">得点{{ gn.runs_scored }} 失点{{ gn.runs_allowed }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 打撃成績 -->
      <section class="mb-8">
        <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3 pl-1">打撃成績</h2>
        <div class="grid grid-cols-3 gap-4 mb-3">
          <div class="bg-white rounded-xl shadow-sm border border-slate-200 border-t-4 border-t-indigo-400 p-5">
            <p class="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-4">打率</p>
            <p class="text-4xl font-black text-indigo-600">{{ fmt3(teamBatting.batting_avg) }}</p>
          </div>
          <div class="bg-white rounded-xl shadow-sm border border-slate-200 border-t-4 border-t-orange-400 p-5">
            <p class="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-4">本塁打</p>
            <p class="text-4xl font-black text-orange-500">{{ teamBatting.homerun ?? '—' }}</p>
          </div>
          <div class="bg-white rounded-xl shadow-sm border border-slate-200 border-t-4 border-t-indigo-400 p-5">
            <p class="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-4">OPS</p>
            <p class="text-4xl font-black text-indigo-600">{{ fmt3(teamBatting.ops) }}</p>
          </div>
        </div>
        <!-- 試合別打撃 -->
        <div
          v-if="teamBatting.by_game_number && teamBatting.by_game_number.length > 1"
          class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden"
        >
          <div
            v-for="gn in teamBatting.by_game_number"
            :key="gn.game_number"
            class="flex items-center gap-4 px-4 py-2 text-sm border-b border-slate-50 last:border-b-0"
          >
            <span class="text-xs font-semibold text-slate-400 w-16 shrink-0">第{{ gn.game_number }}試合</span>
            <span class="text-slate-500 text-xs">{{ gn.game_count }}試合</span>
            <span class="text-slate-400 mx-1">|</span>
            <span class="text-xs text-slate-500">打率 <span class="font-semibold text-indigo-600">{{ fmt3(gn.batting_avg) }}</span></span>
            <span class="text-xs text-slate-500">HR <span class="font-semibold text-orange-500">{{ gn.homerun }}</span></span>
            <span class="text-xs text-slate-500">OPS <span class="font-semibold text-indigo-600">{{ fmt3(gn.ops) }}</span></span>
          </div>
        </div>
      </section>

      <!-- 投手成績 -->
      <section>
        <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3 pl-1">投手成績</h2>
        <div class="grid grid-cols-3 gap-4 mb-3">
          <div class="bg-white rounded-xl shadow-sm border border-slate-200 border-t-4 border-t-sky-400 p-5">
            <p class="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-4">防御率</p>
            <p class="text-4xl font-black text-sky-600">{{ fmt2(teamPitching.era) }}</p>
          </div>
          <div class="bg-white rounded-xl shadow-sm border border-slate-200 border-t-4 border-t-slate-400 p-5">
            <p class="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-4">奪三振</p>
            <p class="text-4xl font-black text-slate-700">{{ teamPitching.strikeouts ?? '—' }}</p>
          </div>
          <div class="bg-white rounded-xl shadow-sm border border-slate-200 border-t-4 border-t-sky-400 p-5">
            <p class="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-4">WHIP</p>
            <p class="text-4xl font-black text-sky-600">{{ fmt2(teamPitching.whip) }}</p>
          </div>
        </div>
        <!-- 試合別投手 -->
        <div
          v-if="teamPitching.by_game_number && teamPitching.by_game_number.length > 1"
          class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden"
        >
          <div
            v-for="gn in teamPitching.by_game_number"
            :key="gn.game_number"
            class="flex items-center gap-4 px-4 py-2 text-sm border-b border-slate-50 last:border-b-0"
          >
            <span class="text-xs font-semibold text-slate-400 w-16 shrink-0">第{{ gn.game_number }}試合</span>
            <span class="text-slate-500 text-xs">{{ gn.game_count }}試合</span>
            <span class="text-slate-400 mx-1">|</span>
            <span class="text-xs text-slate-500">防御率 <span class="font-semibold text-sky-600">{{ fmt2(gn.era) }}</span></span>
            <span class="text-xs text-slate-500">奪三振 <span class="font-semibold text-slate-700">{{ gn.strikeouts }}</span></span>
            <span class="text-xs text-slate-500">WHIP <span class="font-semibold text-sky-600">{{ fmt2(gn.whip) }}</span></span>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { statsApi } from '../api/index.js'
import { useYear } from '../composables/useYear.js'
import YearSelector from '../components/YearSelector.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import ErrorAlert from '../components/ErrorAlert.vue'

const { year } = useYear()
const loading = ref(false)
const error = ref('')
const teamRecord = ref({})
const teamBatting = ref({})
const teamPitching = ref({})

function fmt3(val) {
  return val != null ? val.toFixed(3) : '—'
}
function fmt2(val) {
  return val != null ? val.toFixed(2) : '—'
}

async function fetchAll() {
  loading.value = true
  error.value = ''
  try {
    const [record, batting, pitching] = await Promise.all([
      statsApi.teamRecord(year.value),
      statsApi.teamBatting(year.value),
      statsApi.teamPitching(year.value),
    ])
    teamRecord.value = record
    teamBatting.value = batting
    teamPitching.value = pitching
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(fetchAll)
</script>
