<template>
  <div class="p-6">
    <div v-if="loading" class="text-center py-20">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      <p class="mt-4 text-slate-500">正在进入工作台...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { Loading } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(true)

onMounted(() => {
  if (userStore.isStudent) {
    router.replace('/student/exams')
  } else {
    router.replace('/admin/analytics')
  }
})
</script>
