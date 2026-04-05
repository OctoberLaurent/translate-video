<template>
  <div class="space-y-4">
    <!-- Success banner -->
    <div :class="isDark ? 'bg-green-900/20 border-green-800/40' : 'bg-green-50 border-green-100'" class="flex items-center gap-3 p-4 rounded-notion border">
      <svg class="w-5 h-5 text-notion-green flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
      </svg>
      <div class="flex-1">
        <p class="text-sm font-medium" :class="isDark ? 'text-[#E0E0E0]' : 'text-notion-text'">Sous-titres générés avec succès</p>
        <p v-if="data?.segment_count" :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'" class="text-[11px] mt-0.5">
          {{ data.segment_count }} segments · Langue détectée : {{ data.detected_language }}
        </p>
      </div>
    </div>

    <!-- Download button -->
    <button
      @click="downloadSrt"
      class="w-full flex items-center justify-center gap-2 px-4 py-3 bg-notion-blue text-white rounded-notion
             hover:bg-notion-blue-hover transition-all duration-200 shadow-notion hover:shadow-notion-hover
             font-medium text-sm active:scale-[0.98]"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      Télécharger le fichier .srt
    </button>

    <!-- New video button -->
    <button
      @click="$emit('reset')"
      :class="isDark ? 'text-[#888] hover:text-[#E0E0E0] hover:bg-[#2A2A2A]' : 'text-notion-text-secondary hover:text-notion-text hover:bg-notion-hover'"
      class="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-notion transition-colors text-sm"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
      Traiter une autre vidéo
    </button>
  </div>
</template>

<script setup>
import { getDownloadUrl } from '../services/api.js'

const props = defineProps({
  data: { type: Object, default: null },
  isDark: { type: Boolean, default: false },
})

defineEmits(['reset'])

function downloadSrt() {
  if (!props.data?.srt_path) return
  const filename = props.data.srt_path.split('/').pop()
  const url = getDownloadUrl(filename)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
</script>