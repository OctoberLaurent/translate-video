<template>
  <div class="space-y-8">
    <!-- Step 1: Upload SRT -->
    <section>
      <div class="flex items-center gap-2 mb-4">
        <span :class="[
          'w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-medium',
          srtUploaded ? 'bg-notion-green text-white' : 'bg-notion-blue text-white',
        ]">1</span>
        <h2 class="text-sm font-medium">Fichier SRT</h2>
      </div>

      <!-- SRT drop zone -->
      <div
        @dragover.prevent="isSrtDragging = true"
        @dragleave="isSrtDragging = false"
        @drop.prevent="onSrtDrop"
        @click="srtInputRef?.click()"
        :class="[
          'relative border-2 border-dashed rounded-notion p-8 text-center cursor-pointer transition-all duration-200',
          isSrtDragging
            ? 'border-notion-blue bg-notion-blue/5'
            : srtUploaded
              ? isDark ? 'border-green-800/60 bg-green-900/10' : 'border-green-200 bg-green-50'
              : isDark ? 'border-[#444] hover:border-[#666]' : 'border-notion-border hover:border-notion-blue',
        ]"
      >
        <input ref="srtInputRef" type="file" accept=".srt" class="hidden" @change="onSrtInput" />

        <template v-if="!srtUploaded">
          <div :class="isDark ? 'bg-[#2383E2]/20' : 'bg-notion-blue-bg'" class="w-10 h-10 rounded-notion flex items-center justify-center mx-auto mb-3">
            <svg class="w-5 h-5 text-notion-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
            </svg>
          </div>
          <p class="text-sm font-medium" :class="isDark ? 'text-[#E0E0E0]' : 'text-notion-text'">
            Glissez un fichier .srt ici
          </p>
          <p :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'" class="text-[11px] mt-1">
            ou cliquez pour parcourir
          </p>
        </template>

        <template v-else>
          <div class="flex items-center justify-center gap-2">
            <svg class="w-4 h-4 text-notion-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <span class="text-sm font-medium" :class="isDark ? 'text-green-300' : 'text-green-700'">{{ srtFileName }}</span>
          </div>
          <p v-if="srtSegmentCount" :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'" class="text-[11px] mt-1">
            {{ srtSegmentCount }} segments détectés
          </p>
          <button @click.stop="removeSrt" class="mt-2 text-[11px] text-red-500 hover:text-red-600 underline">Supprimer</button>
        </template>
      </div>
    </section>

    <!-- Step 2: Upload Video (optional) -->
    <section v-if="srtUploaded">
      <div class="flex items-center gap-2 mb-4">
        <span :class="[
          'w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-medium',
          videoUploaded ? 'bg-notion-green text-white' : isDark ? 'bg-[#333] text-[#888]' : 'bg-notion-hover text-notion-text-secondary',
        ]">2</span>
        <h2 class="text-sm font-medium">
          Vidéo source
          <span :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'" class="text-[11px] font-normal ml-1">(optionnel, pour vidéo doublée)</span>
        </h2>
      </div>

      <div
        @dragover.prevent="isVideoDragging = true"
        @dragleave="isVideoDragging = false"
        @drop.prevent="onVideoDrop"
        @click="videoInputRef?.click()"
        :class="[
          'relative border-2 border-dashed rounded-notion p-6 text-center cursor-pointer transition-all duration-200',
          isVideoDragging
            ? 'border-notion-blue bg-notion-blue/5'
            : videoUploaded
              ? isDark ? 'border-green-800/60 bg-green-900/10' : 'border-green-200 bg-green-50'
              : isDark ? 'border-[#444] hover:border-[#666]' : 'border-notion-border hover:border-notion-blue',
        ]"
      >
        <input ref="videoInputRef" type="file" accept=".mp4,.mkv,.avi,.mov,.wmv,.flv,.webm" class="hidden" @change="onVideoInput" />

        <template v-if="!videoUploaded">
          <div :class="isDark ? 'bg-purple-900/30' : 'bg-purple-50'" class="w-8 h-8 rounded-notion flex items-center justify-center mx-auto mb-2">
            <svg class="w-4 h-4 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </div>
          <p class="text-sm" :class="isDark ? 'text-[#ccc]' : 'text-notion-text'">
            Glissez une vidéo ici
          </p>
          <p :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'" class="text-[11px] mt-1">
            Pour générer une vidéo avec l'audio doublé
          </p>
        </template>

        <template v-else>
          <div class="flex items-center justify-center gap-2">
            <svg class="w-4 h-4 text-notion-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <span class="text-sm" :class="isDark ? 'text-green-300' : 'text-green-700'">{{ videoFileName }}</span>
          </div>
          <button @click.stop="removeVideo" class="mt-2 text-[11px] text-red-500 hover:text-red-600 underline">Supprimer</button>
        </template>
      </div>
    </section>

    <!-- Step 3: Voice selection & Generate -->
    <section v-if="srtUploaded">
      <div class="flex items-center gap-2 mb-4">
        <span :class="[
          'w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-medium',
          ttsComplete ? 'bg-notion-green text-white' : 'bg-notion-blue text-white',
        ]">3</span>
        <h2 class="text-sm font-medium">Génération</h2>
      </div>

      <!-- Voice selector -->
      <div class="mb-4">
        <label class="text-[11px] font-medium block mb-1.5" :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'">Voix française</label>
        <select
          v-model="selectedVoice"
          :class="[
            'w-full px-3 py-2 rounded-notion text-sm border outline-none transition-colors',
            isDark
              ? 'bg-[#2A2A2A] border-[#444] text-[#E0E0E0] focus:border-[#2383E2]'
              : 'bg-white border-notion-border text-notion-text focus:border-notion-blue',
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
      </div>

      <!-- TTS Progress -->
      <div v-if="isTTSProcessing" class="space-y-3 mb-4">
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
      <div v-if="ttsError" :class="isDark ? 'bg-red-900/20 border-red-800/40' : 'bg-red-50 border-red-100'" class="flex items-center gap-3 p-3 rounded-notion border mb-4">
        <svg class="w-4 h-4 text-red-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="text-sm text-red-600 dark:text-red-400">{{ ttsError }}</p>
      </div>

      <!-- TTS Success & Downloads -->
      <div v-if="ttsComplete" class="space-y-3">
        <div :class="isDark ? 'bg-purple-900/20 border-purple-800/40' : 'bg-purple-50 border-purple-100'" class="flex items-center gap-3 p-3 rounded-notion border">
          <svg class="w-4 h-4 text-purple-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <p class="text-sm font-medium" :class="isDark ? 'text-purple-300' : 'text-purple-700'">Doublage généré avec succès !</p>
        </div>

        <!-- Download dubbed video -->
        <button
          v-if="ttsResult?.dubbed_video_path"
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
          v-if="ttsResult?.dubbed_audio_path"
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

        <!-- Reset -->
        <button
          @click="resetAll"
          :class="isDark ? 'text-[#888] hover:text-[#E0E0E0] hover:bg-[#2A2A2A]' : 'text-notion-text-secondary hover:text-notion-text hover:bg-notion-hover'"
          class="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-notion transition-colors text-sm mt-2"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Nouveau doublage
        </button>
      </div>

      <!-- Generate button -->
      <button
        v-if="!isTTSProcessing && !ttsComplete"
        @click="startTTS"
        class="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-notion font-medium text-sm
               bg-purple-600 text-white hover:bg-purple-700 transition-all duration-200
               shadow-notion hover:shadow-notion-hover active:scale-[0.98]"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
        </svg>
        Générer le doublage français 🎙️
      </button>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import {
  uploadSrt,
  uploadVideoForTTS,
  createTTSWebSocket,
  downloadDubbedVideo as downloadDubbedVideoApi,
  downloadDubbedAudio as downloadDubbedAudioApi,
} from '../services/api.js'

const TTS_STORAGE_KEY = 'subtranslate-tts-state'

const props = defineProps({
  isDark: { type: Boolean, default: false },
})

// ─── Restore persisted state ───
function loadTTSState() {
  try {
    const raw = localStorage.getItem(TTS_STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch (e) {
    return null
  }
}

function saveTTSState() {
  const state = {
    srtUploaded: srtUploaded.value,
    srtFilePath: srtFilePath.value,
    srtFileName: srtFileName.value,
    srtSegmentCount: srtSegmentCount.value,
    videoUploaded: videoUploaded.value,
    videoFilePath: videoFilePath.value,
    videoFileName: videoFileName.value,
    selectedVoice: selectedVoice.value,
    ttsComplete: ttsComplete.value,
    ttsResult: ttsResult.value,
  }
  try {
    localStorage.setItem(TTS_STORAGE_KEY, JSON.stringify(state))
  } catch (e) {
    console.warn('Failed to save TTS state:', e)
  }
}

function clearTTSState() {
  localStorage.removeItem(TTS_STORAGE_KEY)
}

const savedTTS = loadTTSState()

// SRT state
const srtInputRef = ref(null)
const isSrtDragging = ref(false)
const srtUploaded = ref(savedTTS?.srtUploaded || false)
const srtFilePath = ref(savedTTS?.srtFilePath || null)
const srtFileName = ref(savedTTS?.srtFileName || '')
const srtSegmentCount = ref(savedTTS?.srtSegmentCount || 0)

// Video state
const videoInputRef = ref(null)
const isVideoDragging = ref(false)
const videoUploaded = ref(savedTTS?.videoUploaded || false)
const videoFilePath = ref(savedTTS?.videoFilePath || null)
const videoFileName = ref(savedTTS?.videoFileName || '')

// TTS state
const selectedVoice = ref(savedTTS?.selectedVoice || 'fr-FR-DeniseNeural')
const isTTSProcessing = ref(false)
const ttsProgress = ref(0)
const ttsMessage = ref('')
const ttsComplete = ref(savedTTS?.ttsComplete || false)
const ttsError = ref(null)
const ttsResult = ref(savedTTS?.ttsResult || null)

// Download state
const isDubbedVideoDownloading = ref(false)
const isDubbedAudioDownloading = ref(false)

// ─── Auto-save ───
watch([srtUploaded, srtFilePath, srtFileName, srtSegmentCount, videoUploaded, videoFilePath, videoFileName, selectedVoice, ttsComplete, ttsResult], () => {
  saveTTSState()
}, { deep: true })

// ── SRT handling ──

async function handleSrtFile(file) {
  if (!file || !file.name.toLowerCase().endsWith('.srt')) {
    alert('Veuillez sélectionner un fichier .srt')
    return
  }

  try {
    const result = await uploadSrt(file)
    srtFilePath.value = result.file_path
    srtFileName.value = result.filename
    srtSegmentCount.value = result.segment_count
    srtUploaded.value = true
  } catch (error) {
    alert(`Erreur lors de l'upload du SRT : ${error.message}`)
  }
}

function onSrtDrop(e) {
  isSrtDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) handleSrtFile(file)
}

function onSrtInput(e) {
  const file = e.target?.files?.[0]
  if (file) handleSrtFile(file)
}

function removeSrt() {
  srtUploaded.value = false
  srtFilePath.value = null
  srtFileName.value = ''
  srtSegmentCount.value = 0
  if (srtInputRef.value) srtInputRef.value.value = ''
  resetTTS()
}

// ── Video handling ──

async function handleVideoFile(file) {
  try {
    const result = await uploadVideoForTTS(file)
    videoFilePath.value = result.file_path
    videoFileName.value = result.filename
    videoUploaded.value = true
  } catch (error) {
    alert(`Erreur lors de l'upload de la vidéo : ${error.message}`)
  }
}

function onVideoDrop(e) {
  isVideoDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) handleVideoFile(file)
}

function onVideoInput(e) {
  const file = e.target?.files?.[0]
  if (file) handleVideoFile(file)
}

function removeVideo() {
  videoUploaded.value = false
  videoFilePath.value = null
  videoFileName.value = ''
  if (videoInputRef.value) videoInputRef.value.value = ''
}

// ── TTS Pipeline ──

function startTTS() {
  if (!srtFilePath.value) {
    ttsError.value = 'Aucun fichier SRT disponible.'
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
      srt_path: srtFilePath.value,
      video_path: videoFilePath.value || '',
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

  ws.onerror = () => {
    ttsError.value = 'Erreur de connexion au serveur pour le doublage.'
    isTTSProcessing.value = false
  }

  ws.onclose = () => {
    isTTSProcessing.value = false
  }
}

// ── Downloads ──

async function handleDubbedVideoDownload() {
  if (!ttsResult.value?.dubbed_video_path) return

  const filename = ttsResult.value.dubbed_video_path.split('/').pop()
  isDubbedVideoDownloading.value = true

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
    ttsError.value = error.message || 'Impossible de télécharger la vidéo doublée.'
  } finally {
    isDubbedVideoDownloading.value = false
  }
}

async function handleDubbedAudioDownload() {
  if (!ttsResult.value?.dubbed_audio_path) return

  const filename = ttsResult.value.dubbed_audio_path.split('/').pop()
  isDubbedAudioDownloading.value = true

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
    ttsError.value = error.message || "Impossible de télécharger l'audio doublé."
  } finally {
    isDubbedAudioDownloading.value = false
  }
}

// ── Reset ──

function resetTTS() {
  isTTSProcessing.value = false
  ttsProgress.value = 0
  ttsMessage.value = ''
  ttsComplete.value = false
  ttsError.value = null
  ttsResult.value = null
}

function resetAll() {
  removeSrt()
  removeVideo()
  resetTTS()
}
</script>