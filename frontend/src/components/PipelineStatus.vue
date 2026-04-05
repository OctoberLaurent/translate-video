<template>
  <div class="space-y-4">
    <!-- Steps list -->
    <div class="space-y-1">
      <div
        v-for="step in steps"
        :key="step.key"
        :class="[
          'flex items-center gap-3 px-3 py-2.5 rounded-notion transition-all',
          step.active ? (isDark ? 'bg-notion-blue/10' : 'bg-notion-blue-bg/50') : '',
          step.done ? 'opacity-70' : '',
          step.error ? (isDark ? 'bg-red-900/20' : 'bg-red-50') : '',
        ]"
      >
        <!-- Status icon -->
        <div class="flex-shrink-0 w-5 h-5">
          <!-- Loading spinner -->
          <svg v-if="step.active" class="w-5 h-5 text-notion-blue animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <!-- Done checkmark -->
          <svg v-else-if="step.done" class="w-5 h-5 text-notion-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <!-- Error -->
          <svg v-else-if="step.error" class="w-5 h-5 text-notion-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <!-- Pending -->
          <div v-else :class="isDark ? 'border-[#555]' : 'border-notion-border'" class="w-5 h-5 rounded-full border-2"></div>
        </div>

        <!-- Step info -->
        <div class="flex-1 min-w-0">
          <p :class="[
            'text-sm',
            step.active ? 'font-medium text-notion-blue' : step.error ? 'text-notion-red' : isDark ? 'text-[#E0E0E0]' : 'text-notion-text',
          ]">
            {{ step.label }}
          </p>
          <p v-if="step.message" :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'" class="text-[11px] mt-0.5 truncate">
            {{ step.message }}
          </p>
        </div>

        <!-- Progress percentage -->
        <span v-if="step.active && step.progress > 0" class="text-xs text-notion-blue font-medium">
          {{ step.progress }}%
        </span>
      </div>
    </div>

    <!-- Error message -->
    <div v-if="errorMessage" :class="isDark ? 'bg-red-900/20 border-red-800/40' : 'bg-red-50 border-red-100'" class="p-3 rounded-notion border">
      <p class="text-xs text-notion-red">{{ errorMessage }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const props = defineProps({ isDark: Boolean })

const errorMessage = ref('')

const steps = reactive([
  { key: 'extraction', label: 'Extraction audio', active: false, done: false, error: false, progress: 0, message: '' },
  { key: 'transcription', label: 'Transcription Whisper', active: false, done: false, error: false, progress: 0, message: '' },
  { key: 'translation', label: 'Traduction en français', active: false, done: false, error: false, progress: 0, message: '' },
  { key: 'srt', label: 'Génération du fichier SRT', active: false, done: false, error: false, progress: 0, message: '' },
])

function resetSteps() {
  steps.forEach(s => {
    s.active = false
    s.done = false
    s.error = false
    s.progress = 0
    s.message = ''
  })
  errorMessage.value = ''
}

function updateStep(stepKey, data) {
  const step = steps.find(s => s.key === stepKey)
  if (!step) return

  if (data.type === 'progress') {
    step.active = true
    step.done = data.progress === 100
    step.progress = data.progress
    step.message = data.message
    const idx = steps.indexOf(step)
    for (let i = 0; i < idx; i++) {
      steps[i].active = false
      steps[i].done = true
    }
  } else if (data.type === 'error') {
    step.active = false
    step.error = true
    step.message = data.message
    errorMessage.value = data.message
  }
}

function markComplete(data) {
  steps.forEach(s => {
    s.active = false
    s.done = true
    s.progress = 100
  })
}

defineExpose({ resetSteps, updateStep, markComplete, errorMessage })
</script>