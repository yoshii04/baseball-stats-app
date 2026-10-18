/**
 * アプリ全体で共有する年度選択 composable。
 * import { useYear } from '@/composables/useYear' で利用。
 */
import { ref } from 'vue'

const year = ref(null) // null = 通算（デフォルト）

export function useYear() {
  return { year }
}
