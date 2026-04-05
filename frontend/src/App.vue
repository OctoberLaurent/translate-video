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
            <p :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'" class="text-[11px]">Sous-titres automatiques en français</p>
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
          <!-- Sun icon (shown in dark mode) -->
          <svg v-if="isDark" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <!-- Moon icon (shown in light mode) -->
          <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
          </svg>
        </button>
      </div>
    </header>

    <!-- Main content -->
    <main class="max-w-2xl mx-auto px-6 py-10 space-y-10">

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
        <ConfigPanel :is-dark="isDark" @config-changed="onConfigChanged" />

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
import { ref, computed } from 'vue'
import DropZone from './components/DropZone.vue'
import ConfigPanel from './components/ConfigPanel.vue'
import PipelineStatus from './components/PipelineStatus.vue'
import DownloadSection from './components/DownloadSection.vue'
import { uploadVideo, createPipelineWebSocket } from './services/api.js'

// Dark mode — detect system preference on startup
const isDark = ref(false)

function initDarkMode() {
  const saved = localStorage.getItem('subtranslate-theme')
  if (saved) {
    isDark.value = saved === 'dark'
  } else {
    isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
  }
  document.documentElement.classList.toggle('dark', isDark.value)

  // Listen for system theme changes
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

// State
const currentStep = ref(1)
const selectedFile = ref(null)
const uploadedFilePath = ref(null)
const config = ref({
  whisperModel: 'base',
  llmModel: '',
  whisperTask: 'translate',
  lmStudioPort: 7890,
  translationPrompt: '',
})
const isProcessing = ref(false)
const pipelineComplete = ref(false)
const pipelineResult = ref(null)
const pipelineStatus = ref(null)

const canStartPipeline = computed(() => {
  return uploadedFilePath.value && config.value.llmModel
})

function onFileSelected(file) {
  selectedFile.value = file
  uploadFile(file)
}

function onFileRemoved() {
  selectedFile.value = null
  uploadedFilePath.value = null
  currentStep.value = 1
}

function onConfigChanged(newConfig) {
  config.value = newConfig
}

async function uploadFile(file) {
  try {
    const result = await uploadVideo(file)
    uploadedFilePath.value = result.file_path
    currentStep.value = 2
  } catch (error) {
    alert(`Erreur lors de l'upload : ${error.message}`)
  }
}

async function startPipeline() {
  if (!canStartPipeline.value || isProcessing.value) return

  isProcessing.value = true
  pipelineComplete.value = false
  pipelineResult.value = null
  currentStep.value = 3

  if (pipelineStatus.value) {
    pipelineStatus.value.resetSteps()
  }

  const ws = createPipelineWebSocket()

  ws.onopen = () => {
    // Send pipeline configuration
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
        ws.close()
      } else if (data.type === 'complete') {
        pipelineStatus.value?.markComplete(data)
        pipelineResult.value = data.data
        pipelineComplete.value = true
        isProcessing.value = false
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
  }

  ws.onclose = () => {
    isProcessing.value = false
  }
}

function resetAll() {
  currentStep.value = 1
  selectedFile.value = null
  uploadedFilePath.value = null
  isProcessing.value = false
  pipelineComplete.value = false
  pipelineResult.value = null
}
</script>