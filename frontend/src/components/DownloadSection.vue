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

    <!-- Download SRT button -->
    <button
      @click="downloadSrt"
      :disabled="isDownloading"
      :class="isDownloading ? 'opacity-70 cursor-wait' : ''"
      class="w-full flex items-center justify-center gap-2 px-4 py-3 bg-notion-blue text-white rounded-notion
             hover:bg-notion-blue-hover transition-all duration-200 shadow-notion hover:shadow-notion-hover
             font-medium text-sm active:scale-[0.98]"
    >
      <svg v-if="isDownloading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
      </svg>
      <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      {{ isDownloading ? 'Téléchargement en cours...' : 'Télécharger le fichier .srt' }}
    </button>

    <!-- Divider -->
    <div :class="isDark ? 'border-[#333]' : 'border-notion-border'" class="border-t"></div>

    <!-- TTS Dubbing Section -->
    <div class="space-y-3">
      <div class="flex items-center gap-2">
        <div :class="isDark ? 'bg-purple-900/30' : 'bg-purple-50'" class="w-6 h-6 rounded-full flex items-center justify-center">
          <svg class="w-3.5 h-3.5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
          </svg>
        </div>
        <h3 class="text-sm font-medium" :class="isDark ? 'text-[#E0E0E0]' : 'text-notion-text'">Doublage français</h3>
      </div>

      <!-- TTS Progress -->
      <div v-if="isTTSProcessing" class="space-y-2">
        <div class="flex items-center gap-2">
          <svg class="w-4 h-4 animate-spin text-purple-500" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span class="text-sm" :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'">{{ ttsMessage }}</span>
        </div>
        <!-- Progress bar -->
        <div :class="isDark ? 'bg-[#333]' : 'bg-notion-hover'" class="w-full h-1.5 rounded-full overflow-hidden">
          <div
            class="h-full bg-purple-500 rounded-full transition-all duration-300"
            :style="{ width: `${ttsProgress}%` }"
          ></div>
        </div>
      </div>

      <!-- TTS Error -->
      <div v-if="ttsError" :class="isDark ? 'bg-red-900/20 border-red-800/40' : 'bg-red-50 border-red-100'" class="flex items-center gap-3 p-3 rounded-notion border">
        <svg class="w-4 h-4 text-red-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="text-sm text-red-600 dark:text-red-400">{{ ttsError }}</p>
      </div>

      <!-- TTS Success & Downloads (from manual TTS trigger) -->
      <div v-if="ttsComplete" class="space-y-3">
        <div :class="isDark ? 'bg-purple-900/20 border-purple-800/40' : 'bg-purple-50 border-purple-100'" class="flex items-center gap-3 p-3 rounded-notion border">
          <svg class="w-4 h-4 text-purple-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <p class="text-sm font-medium" :class="isDark ? 'text-purple-300' : 'text-purple-700'">Doublage généré avec succès</p>
        </div>

        <!-- Download dubbed video -->
        <button
          v-if="effectiveDubbedVideoPath"
          @click="handleDubbedVideoDownload"
          :disabled="isDubbedVideoDownloading"
          :class="[
            'w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-notion font-medium text-sm',
            'transition-all duration-200 active:scale-[0.98]',
            isDubbedVideoDownloading ? 'opacity-70 cursor-wait' : '',
            isDark
              ? 'bg-purple-600/20 text-purple-300 hover:bg-purple-600/30 border border-purple-700/40'
              : 'bg-purple-600 text-white hover:bg-purple-700 shadow-notion hover:shadow-notion-hover',
          ]"
        >
          <svg v-if="isDubbedVideoDownloading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          {{ isDubbedVideoDownloading ? 'Téléchargement...' : 'Télécharger la vidéo doublée' }}
        </button>

        <!-- Download dubbed audio only -->
        <button
          v-if="effectiveDubbedAudioPath"
          @click="handleDubbedAudioDownload"
          :disabled="isDubbedAudioDownloading"
          :class="[
            'w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-notion text-sm',
            'transition-all duration-200 active:scale-[0.98]',
            isDubbedAudioDownloading ? 'opacity-70 cursor-wait' : '',
            isDark
              ? 'text-purple-300 hover:bg-purple-600/10 border border-purple-700/30'
              : 'text-purple-600 hover:bg-purple-50 border border-purple-200',
          ]"
        >
          <svg v-if="isDubbedAudioDownloading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
          </svg>
          {{ isDubbedAudioDownloading ? 'Téléchargement...' : "Télécharger l'audio français (.wav)" }}
        </button>
      </div>

      <!-- Voice selector -->
      <div v-if="!isTTSProcessing && !ttsComplete && !data?.dubbed_audio_path" class="space-y-1.5">
        <label class="text-xs font-medium" :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'">Voix française</label>
        <div class="relative">
          <select
            v-model="selectedVoice"
            :class="[
              'w-full appearance-none rounded-notion px-3 py-2 text-sm transition-colors',
              'focus:outline-none focus:ring-1 focus:ring-purple-400/30',
              isDark
                ? 'bg-[#2A2A2A] border border-[#444] text-[#E0E0E0] focus:border-purple-500'
                : 'bg-white border border-notion-border text-notion-text focus:border-purple-500',
            ]"
          >
            <option value="fr-FR-DeniseNeural">Denise (féminine)</option>
            <option value="fr-FR-HenriNeural">Henri (masculin)</option>
            <option value="fr-FR-EloiseNeural">Eloise (féminine, multilingue)</option>
            <option value="fr-FR-JeanNeural">Jean (masculin)</option>
            <option value="fr-FR-SuzanneNeural">Suzanne (féminine)</option>
            <option value="fr-BE-CharlineNeural">Charline (belge, féminine)</option>
            <option value="fr-CA-ThierryNeural">Thierry (canadien, masculin)</option>
            <option value="fr-CA-SylvieNeural">Sylvie (canadienne, féminine)</option>
            <option value="fr-CH-ArianeNeural">Ariane (suisse, féminine)</option>
            <option value="fr-CH-GuillaumeNeural">Guillaume (suisse, masculin)</option>
          </select>
          <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none" :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      <!-- Generate dubbing button (only if pipeline didn't already include TTS) -->
      <button
        v-if="!isTTSProcessing && !ttsComplete && !data?.dubbed_audio_path"
        @click="startTTS"
        :class="[
          'w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-notion font-medium text-sm',
          'transition-all duration-200 active:scale-[0.98]',
          isDark
            ? 'bg-purple-600/20 text-purple-300 hover:bg-purple-600/30 border border-purple-700/40'
            : 'bg-purple-50 text-purple-600 hover:bg-purple-100 border border-purple-200',
        ]"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
        </svg>
        Générer le doublage français 🎙️
      </button>
    </div>

    <!-- Download error -->
    <div v-if="downloadError" :class="isDark ? 'bg-red-900/20 border-red-800/40' : 'bg-red-50 border-red-100'" class="flex items-center gap-3 p-3 rounded-notion border">
      <svg class="w-4 h-4 text-red-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <div class="flex-1">
        <p class="text-sm text-red-600 dark:text-red-400">{{ downloadError }}</p>
        <p class="text-[11px] mt-0.5" :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'">
          Vérifiez que le backend est toujours en cours d'exécution (terminal).
        </p>
      </div>
    </div>

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
import { ref, computed, watch } from 'vue'
import {
  downloadSrtFile,
  downloadDubbedVideo as downloadDubbedVideoApi,
  downloadDubbedAudio as downloadDubbedAudioApi,
  createTTSWebSocket,
} from '../services/api.js'

const props = defineProps({
  data: { type: Object, default: null },
  isDark: { type: Boolean, default: false },
  voice: { type: String, default: 'fr-FR-DeniseNeural' },
})

defineEmits(['reset'])

const isDownloading = ref(false)
const downloadError = ref(null)

// TTS state
const isTTSProcessing = ref(false)
const ttsProgress = ref(0)
const ttsMessage = ref('')
const ttsComplete = ref(false)
const ttsError = ref(null)
const ttsResult = ref(null)

// Voice selector (initialized from prop)
const selectedVoice = ref(props.voice)

// Dubbed downloads state
const isDubbedVideoDownloading = ref(false)
const isDubbedAudioDownloading = ref(false)

// Reset TTS state when video changes (new srt_path) or data is cleared
watch(() => props.data?.srt_path, (newPath, oldPath) => {
  if (!newPath || (oldPath && newPath !== oldPath)) {
    ttsComplete.value = false
    ttsResult.value = null
    ttsError.value = null
    ttsProgress.value = 0
    ttsMessage.value = ''
    isTTSProcessing.value = false
  }
})

// Auto-detect when pipeline already includes dubbed files
watch(() => props.data, (newData) => {
  if (newData?.dubbed_audio_path) {
    ttsComplete.value = true
    ttsResult.value = newData
  }
}, { immediate: true })

// Use pipeline-provided paths or TTS-generated paths
const effectiveDubbedVideoPath = computed(() => {
  return props.data?.dubbed_video_path || ttsResult.value?.dubbed_video_path
})

const effectiveDubbedAudioPath = computed(() => {
  return props.data?.dubbed_audio_path || ttsResult.value?.dubbed_audio_path
})

async function downloadSrt() {
  if (!props.data?.srt_path || isDownloading.value) return

  const filename = props.data.srt_path.split('/').pop()
  isDownloading.value = true
  downloadError.value = null

  try {
    const { blob, filename: downloadName } = await downloadSrtFile(filename)

    const blobUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = downloadName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    setTimeout(() => URL.revokeObjectURL(blobUrl), 5000)
  } catch (error) {
    console.error('Download error:', error)
    downloadError.value = error.message || 'Impossible de télécharger le fichier.'
  } finally {
    isDownloading.value = false
  }
}

function startTTS() {
  if (!props.data?.srt_path) {
    ttsError.value = 'Aucun fichier SRT disponible pour le doublage.'
    return
  }

  isTTSProcessing.value = true
  ttsProgress.value = 0
  ttsMessage.value = 'Connexion au serveur TTS...'
  ttsComplete.value = false
  ttsError.value = null
  ttsResult.value = null

  const ws = createTTSWebSocket()

  ws.onopen = () => {
    ws.send(JSON.stringify({
      srt_path: props.data.srt_path,
      video_path: props.data.video_path || '',
      voice: selectedVoice.value,
    }))
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)

      if (data.type === 'progress') {
        ttsProgress.value = data.progress || 0
        ttsMessage.value = data.message || ''
      } else if (data.type === 'error') {
        ttsError.value = data.message || 'Erreur lors du doublage.'
        isTTSProcessing.value = false
        ws.close()
      } else if (data.type === 'complete') {
        ttsResult.value = data.data
        ttsComplete.value = true
        isTTSProcessing.value = false
        ttsProgress.value = 100
        ttsMessage.value = ''
        ws.close()
      }
    } catch (e) {
      console.error('Error parsing TTS WebSocket message:', e)
    }
  }

  ws.onerror = (error) => {
    console.error('TTS WebSocket error:', error)
    ttsError.value = 'Erreur de connexion au serveur pour le doublage.'
    isTTSProcessing.value = false
  }

  ws.onclose = () => {
    isTTSProcessing.value = false
  }
}

async function handleDubbedVideoDownload() {
  if (!ttsResult.value?.dubbed_video_path) return

  const filename = ttsResult.value.dubbed_video_path.split('/').pop()
  isDubbedVideoDownloading.value = true
  downloadError.value = null

  try {
    const { blob, filename: downloadName } = await downloadDubbedVideoApi(filename)

    const blobUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = downloadName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    setTimeout(() => URL.revokeObjectURL(blobUrl), 5000)
  } catch (error) {
    console.error('Dubbed video download error:', error)
    downloadError.value = error.message || 'Impossible de télécharger la vidéo doublée.'
  } finally {
    isDubbedVideoDownloading.value = false
  }
}

async function handleDubbedAudioDownload() {
  if (!ttsResult.value?.dubbed_audio_path) return

  const filename = ttsResult.value.dubbed_audio_path.split('/').pop()
  isDubbedAudioDownloading.value = true
  downloadError.value = null

  try {
    const { blob, filename: downloadName } = await downloadDubbedAudioApi(filename)

    const blobUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = downloadName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    setTimeout(() => URL.revokeObjectURL(blobUrl), 5000)
  } catch (error) {
    console.error('Dubbed audio download error:', error)
    downloadError.value = error.message || "Impossible de télécharger l'audio doublé."
  } finally {
    isDubbedAudioDownloading.value = false
  }
}
</script>