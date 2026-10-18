<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-sm text-center">
      <h1 class="text-2xl font-bold mb-2 text-gray-800">野球成績管理</h1>
      <p class="text-gray-500 mb-6 text-sm">チームメンバー専用</p>

      <div v-if="error" class="mb-4 p-3 bg-red-50 text-red-600 rounded text-sm">
        {{ error }}
      </div>

      <div id="g_id_onload"
        :data-client_id="clientId"
        data-callback="handleGoogleLogin"
        data-auto_prompt="false"
      />
      <div class="g_id_signin"
        data-type="standard"
        data-shape="rectangular"
        data-theme="outline"
        data-text="sign_in_with"
        data-size="large"
        data-locale="ja"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const error = ref('')
const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? ''

onMounted(() => {
  // Google GSI スクリプトの読み込み
  if (!document.getElementById('gsi-script')) {
    const script = document.createElement('script')
    script.id = 'gsi-script'
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.defer = true
    document.head.appendChild(script)
  }

  // コールバックをグローバルに登録
  window.handleGoogleLogin = (response) => {
    if (response.credential) {
      sessionStorage.setItem('id_token', response.credential)
      router.push('/')
    } else {
      error.value = 'ログインに失敗しました。再度お試しください。'
    }
  }
})
</script>
