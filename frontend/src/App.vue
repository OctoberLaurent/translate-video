<template>
  <div :class="[isDark ? 'dark bg-[#191919] text-[#E0E0E0]' : 'bg-white text-notion-text']" class="min-h-screen transition-colors duration-300">
    <!-- Header -->
    <header :class="isDark ? 'border-[#333]' : 'border-notion-border'" class="border-b">
      <div class="max-w-2xl mx-auto px-6 py-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div :class="isDark ? 'bg-[#2383E2]/20' : 'bg-notion-blue-bg'" class="w-8 h-8 rounded-notion flex items-center justify-center">
            <svg :class="isDark ? 'text-blue-400' : 'text-notion-blue'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
            </svg>
          </div>
          <div>
            <h1 class="text-sm font-semibold">SubTranslate</h1>
            <p :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'" class="text-[11px]">Sous-titres et doublage automatiques</p>
          </div>
        </div>
        <!-- Dark mode toggle -->
        <button
          @click="toggleDark"
          :class="[
            'p-2 rounded-notion transition-colors',
            isDark ? 'hover:bg-[#333] text-[#888]' : 'hover:bg-notion-hover text-notion-text-secondary',
          ]"
          :title="isDark ? 'Mode clair' : 'Mode sombre'"
        >
          <svg v-if="isDark" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
          </svg>
        </button>
      </div>

      <!-- Tabs -->
      <div class="max-w-2xl mx-auto px-6">
        <div class="flex gap-6">
          <button
            @click="switchTab('subtitles')"
            :class="[
              'pb-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'subtitles'
                ? isDark ? 'border-[#2383E2] text-[#2383E2]' : 'border-notion-blue text-notion-blue'
                : isDark ? 'border-transparent text-[#888] hover:text-[#bbb]' : 'border-transparent text-notion-text-secondary hover:text-notion-text',
            ]"
          >
            <span class="flex items-center gap-1.5">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
              </svg>
              Sous-titres
            </span>
          </button>
          <button
            @click="switchTab('tts')"
            :class="[
              'pb-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'tts'
                ? isDark ? 'border-purple-500 text-purple-400' : 'border-purple-600 text-purple-600'
                : isDark ? 'border-transparent text-[#888] hover:text-[#bbb]' : 'border-transparent text-notion-text-secondary hover:text-notion-text',
            ]"
          >
            <span class="flex items-center gap-1.5">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
              Doublage SRT
            </span>
          </button>
        </div>
      </div>
    </header>

    <!-- Main content -->
    <main class="max-w-2xl mx-auto px-6 py-10 space-y-10">

      <!-- Tab: Subtitles -->
      <template v-if="activeTab === 'subtitles'">
        <!-- Step 1: Upload -->
        <section>
          <div class="flex items-center gap-2 mb-4">
            <span :class="[
              'w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-medium',
              currentStep >= 1 ? 'bg-notion-blue text-white' : isDark ? 'bg-[#333] text-[#888]' : 'bg-notion-hover text-notion-text-secondary',
            ]">1</span>
            <h2 class="text-sm font-medium">Vidéo source</h2>
          </div>
          <DropZone
            :is-dark="isDark"
            :initial-file-name="uploadedFileName"
            @file-selected="onFileSelected"
            @file-removed="onFileRemoved"
          />
        </section>

        <!-- Step 2: Config -->
        <section v-if="currentStep >= 2" class="transition-all duration-300">
          <div class="flex items-center gap-2 mb-4">
            <span :class="[
              'w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-medium',
              currentStep >= 2 ? 'bg-notion-blue text-white' : isDark ? 'bg-[#333] text-[#888]' : 'bg-notion-hover text-notion-text-secondary',
            ]">2</span>
            <h2 class="text-sm font-medium">Paramètres</h2>
          </div>
          <ConfigPanel :is-dark="isDark" :initial-config="config" @config-changed="onConfigChanged" />

          <!-- Start button -->
          <button
            @click="startPipeline"
            :disabled="!canStartPipeline || isProcessing"
            :class="[
              'mt-6 w-full flex items-center justify-center gap-2 px-4 py-3 rounded-notion font-medium text-sm',
              'transition-all duration-200',
              canStartPipeline && !isProcessing
                ? 'bg-notion-blue text-white hover:bg-notion-blue-hover shadow-notion hover:shadow-notion-hover active:scale-[0.98]'
                : isDark ? 'bg-[#333] text-[#666] cursor-not-allowed' : 'bg-notion-hover text-notion-text-secondary cursor-not-allowed',
            ]"
          >
            <svg v-if="isProcessing" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            {{ isProcessing ? 'Traitement en cours...' : 'Générer les sous-titres' }}
          </button>
        </section>

        <!-- Step 3: Pipeline Progress -->
        <section v-if="currentStep >= 3" class="transition-all duration-300">
          <div class="flex items-center gap-2 mb-4">
            <span :class="[
              'w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-medium',
              pipelineComplete ? 'bg-notion-green text-white' : 'bg-notion-blue text-white',
            ]">3</span>
            <h2 class="text-sm font-medium">
              {{ pipelineComplete ? 'Terminé' : 'Traitement' }}
            </h2>
          </div>

          <PipelineStatus ref="pipelineStatus" :is-dark="isDark" />

          <!-- Download section (shown when complete) -->
          <div v-if="pipelineComplete" class="mt-6">
            <DownloadSection :data="pipelineResult" :is-dark="isDark" @reset="resetAll" />
          </div>
        </section>
      </template>

      <!-- Tab: TTS from SRT -->
      <template v-if="activeTab === 'tts'">
        <TTSView :is-dark="isDark" />
      </template>

    </main>

    <!-- Footer -->
    <footer :class="isDark ? 'border-[#333]' : 'border-notion-border'" class="border-t mt-16">
      <div class="max-w-2xl mx-auto px-6 py-4">
        <p :class="isDark ? 'text-[#666]' : 'text-notion-text-secondary'" class="text-[11px] text-center">
          Traitement 100% local · Vos données restent sur votre machine
        </p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import DropZone from './components/DropZone.vue'
import ConfigPanel from './components/ConfigPanel.vue'
import PipelineStatus from './components/PipelineStatus.vue'
import DownloadSection from './components/DownloadSection.vue'
import TTSView from './components/TTSView.vue'
import { uploadVideo, createPipelineWebSocket } from './services/api.js'

// ─── Persistence helpers ───
const STORAGE_KEY = 'subtranslate-state'

function saveState() {
  const state = {
    activeTab: activeTab.value,
    currentStep: currentStep.value,
    uploadedFilePath: uploadedFilePath.value,
    uploadedFileName: uploadedFileName.value,
    config: config.value,
    isProcessing: isProcessing.value,
    pipelineComplete: pipelineComplete.value,
    pipelineResult: pipelineResult.value,
  }
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch (e) {
    console.warn('Failed to save state:', e)
  }
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch (e) {
    return null
  }
}

function clearState() {
  localStorage.removeItem(STORAGE_KEY)
}

// ─── Dark mode ───
const isDark = ref(false)

function initDarkMode() {
  const saved = localStorage.getItem('subtranslate-theme')
  if (saved) {
    isDark.value = saved === 'dark'
  } else {
    isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
  }
  document.documentElement.classList.toggle('dark', isDark.value)

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (!localStorage.getItem('subtranslate-theme')) {
      isDark.value = e.matches
      document.documentElement.classList.toggle('dark', isDark.value)
    }
  })
}

initDarkMode()

function toggleDark() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('subtranslate-theme', isDark.value ? 'dark' : 'light')
}

// ─── Restore persisted state ───
const savedState = loadState()

// ─── Tab state ───
const activeTab = ref(savedState?.activeTab || 'subtitles')

function switchTab(tab) {
  activeTab.value = tab
  saveState()
}

// ─── Pipeline state ───
const currentStep = ref(savedState?.currentStep || 1)
const selectedFile = ref(null)
const uploadedFilePath = ref(savedState?.uploadedFilePath || null)
const uploadedFileName = ref(savedState?.uploadedFileName || '')
const config = ref(savedState?.config || {
  whisperModel: 'base',
  llmModel: '',
  whisperTask: 'translate',
  lmStudioPort: 7890,
  translationPrompt: '',
})
const isProcessing = ref(false) // Never restore processing state
const pipelineComplete = ref(savedState?.pipelineComplete || false)
const pipelineResult = ref(savedState?.pipelineResult || null)
const pipelineStatus = ref(null)

const canStartPipeline = computed(() => {
  return uploadedFilePath.value && config.value.llmModel
})

// ─── Auto-save on state changes ───
watch([activeTab, currentStep, uploadedFilePath, uploadedFileName, config, pipelineComplete, pipelineResult], () => {
  saveState()
}, { deep: true })

// ─── File handling ───

function onFileSelected(file) {
  selectedFile.value = file
  uploadFile(file)
}

function onFileRemoved() {
  selectedFile.value = null
  uploadedFilePath.value = null
  uploadedFileName.value = ''
  currentStep.value = 1
  pipelineComplete.value = false
  pipelineResult.value = null
  saveState()
}

async function uploadFile(file) {
  try {
    const result = await uploadVideo(file)
    uploadedFilePath.value = result.file_path
    uploadedFileName.value = file.name
    currentStep.value = 2
    saveState()
  } catch (error) {
    alert(`Erreur lors de l'upload : ${error.message}`)
  }
}

function onConfigChanged(newConfig) {
  config.value = newConfig
  saveState()
}

// ─── Pipeline execution ───

async function startPipeline() {
  if (!canStartPipeline.value || isProcessing.value) return

  isProcessing.value = true
  pipelineComplete.value = false
  pipelineResult.value = null
  currentStep.value = 3
  saveState()

  if (pipelineStatus.value) {
    pipelineStatus.value.resetSteps()
  }

  const ws = createPipelineWebSocket()

  ws.onopen = () => {
    ws.send(JSON.stringify({
      file_path: uploadedFilePath.value,
      whisper_model: config.value.whisperModel,
      llm_model: config.value.llmModel,
      whisper_task: config.value.whisperTask,
      lm_studio_port: config.value.lmStudioPort,
      translation_prompt: config.value.translationPrompt || null,
    }))
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)

      if (data.type === 'progress') {
        pipelineStatus.value?.updateStep(data.step, data)
      } else if (data.type === 'error') {
        pipelineStatus.value?.updateStep(data.step, data)
        isProcessing.value = false
        saveState()
        ws.close()
      } else if (data.type === 'complete') {
        pipelineStatus.value?.markComplete(data)
        pipelineResult.value = data.data
        pipelineComplete.value = true
        isProcessing.value = false
        saveState()
        ws.close()
      }
    } catch (e) {
      console.error('Error parsing WebSocket message:', e)
    }
  }

  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
    isProcessing.value = false
    pipelineStatus.value?.updateStep('extraction', {
      type: 'error',
      step: 'pipeline',
      message: 'Erreur de connexion au serveur backend.',
    })
    saveState()
  }

  ws.onclose = () => {
    isProcessing.value = false
    saveState()
  }
}

function resetAll() {
  currentStep.value = 1
  selectedFile.value = null
  uploadedFilePath.value = null
  uploadedFileName.value = ''
  isProcessing.value = false
  pipelineComplete.value = false
  pipelineResult.value = null
  saveState()
}
</script>