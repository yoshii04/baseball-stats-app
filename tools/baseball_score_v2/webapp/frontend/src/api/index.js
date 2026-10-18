/**
 * API 通信レイヤー
 * Vite の dev proxy (/api → http://localhost:8000) を利用するため baseURL は空。
 * 本番ビルドでは VITE_API_BASE_URL 環境変数で上書き可能。
 */
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '',
  timeout: 10000,
})

// リクエスト: sessionStorage の id_token を Authorization ヘッダーに付与
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('id_token')
  if (token) {
    config.headers = config.headers ?? {}
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res.data,
  (err) => {
    console.error('API Error:', err.response?.data ?? err.message)
    if (err.response?.status === 401) {
      sessionStorage.removeItem('id_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

/** year が null のとき year パラメーターを省略するヘルパー */
function yearParam(year) {
  return year != null ? { year } : {}
}

// ---------- 選手 ----------
export const playersApi = {
  list:  (year)       => api.get('/api/players',             { params: { ...yearParam(year) } }),
  get:   (id)         => api.get(`/api/players/${id}`),
  stats: (id, year)   => api.get(`/api/players/${id}/stats`, { params: { ...yearParam(year) } }),
}

// ---------- 試合 ----------
export const gamesApi = {
  list: (year, month) => api.get('/api/games',       { params: { ...yearParam(year), ...(month ? { month } : {}) } }),
  get:  (id)          => api.get(`/api/games/${id}`),
}

// ---------- 成績統計 ----------
export const statsApi = {
  season:       (year)           => api.get('/api/stats/season',        { params: { ...yearParam(year) } }),
  ranking:      (year, limit=10) => api.get('/api/stats/ranking',       { params: { ...yearParam(year), limit } }),
  teamBatting:  (year)           => api.get('/api/stats/team-batting',  { params: { ...yearParam(year) } }),
  teamPitching: (year)           => api.get('/api/stats/team-pitching', { params: { ...yearParam(year) } }),
  teamRecord:   (year)           => api.get('/api/stats/team-record',   { params: { ...yearParam(year) } }),
}

// ---------- 投手 ----------
export const pitchersApi = {
  list:  (year)           => api.get('/api/pitchers',             { params: { ...yearParam(year) } }),
  stats: (pitcherId, year) => api.get(`/api/pitchers/${pitcherId}/stats`, { params: { ...yearParam(year) } }),
}

// ---------- 実行履歴 ----------
export const historyApi = {
  list: ({ date, step, last } = {}) => api.get('/api/history', {
    params: {
      ...(date ? { date } : {}),
      ...(step ? { step } : {}),
      ...(last != null ? { last } : {}),
    },
  }),
}

// ---------- 分析 ----------
export const analyticsApi = {
  hitDirection: (year, playerId) => api.get('/api/analytics/hit-direction', {
    params: { ...yearParam(year), ...(playerId ? { player_id: playerId } : {}) },
  }),
  battingTrend: (year, playerId) => api.get('/api/analytics/batting-trend', {
    params: { ...yearParam(year), ...(playerId ? { player_id: playerId } : {}) },
  }),
}
