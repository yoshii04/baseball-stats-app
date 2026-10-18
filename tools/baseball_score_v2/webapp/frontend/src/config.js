/**
 * 画面表示用の設定。
 * 値はビルド時の環境変数（.env.local / .env.production）から取得する。
 */
export const TEAM_NAME = import.meta.env.VITE_TEAM_NAME || '自チーム'

/**
 * デモモード（合成データの画面確認用）。認証画面を飛ばし、画面上部に注記を出す。
 * バックエンドも DEMO_MODE=true のときだけ認証を省略する（demo/docker-compose.yml）。
 */
export const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true'
