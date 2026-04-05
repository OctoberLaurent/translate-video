<template>
  <div class="space-y-6">
    <!-- Section title -->
    <h3 class="text-sm font-medium" :class="isDark ? 'text-[#E0E0E0]' : 'text-notion-text'">Configuration</h3>

    <!-- Whisper Model Selection -->
    <div class="space-y-2">
      <label class="text-xs font-medium" :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'">Modèle Whisper</label>
      <div class="relative">
        <select
          v-model="selectedWhisperModel"
          :class="[
            'w-full appearance-none rounded-notion px-3 py-2.5 text-sm transition-colors',
            'focus:outline-none focus:ring-1 focus:ring-notion-blue/20',
            isDark
              ? 'bg-[#2A2A2A] border border-[#444] text-[#E0E0E0] focus:border-notion-blue'
              : 'bg-white border border-notion-border text-notion-text focus:border-notion-blue',
          ]"
        >
          <option v-for="model in whisperModels" :key="model" :value="model">
            {{ modelLabels[model] || model }}
          </option>
        </select>
        <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none" :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </div>
      <p class="text-[11px]" :class="isDark ? 'text-[#666]' : 'text-notion-text-secondary'">
        {{ modelDescriptions[selectedWhisperModel] }}
      </p>
    </div>

    <!-- Whisper Task -->
    <div class="space-y-2">
      <label class="text-xs font-medium" :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'">Mode de transcription</label>
      <div class="flex gap-3">
        <button
          v-for="option in taskOptions"
          :key="option.value"
          @click="selectedTask = option.value"
          :class="[
            'flex-1 px-3 py-2.5 rounded-notion text-xs font-medium transition-all',
            selectedTask === option.value
              ? isDark
                ? 'bg-notion-blue/20 text-blue-400 border border-notion-blue/40'
                : 'bg-notion-blue-bg text-notion-blue border border-notion-blue/30'
              : isDark
                ? 'bg-[#2A2A2A] text-[#888] border border-[#444] hover:bg-[#333]'
                : 'bg-white text-notion-text-secondary border border-notion-border hover:bg-notion-hover',
          ]"
        >
          {{ option.label }}
        </button>
      </div>
      <p class="text-[11px]" :class="isDark ? 'text-[#666]' : 'text-notion-text-secondary'">
        {{ selectedTask === 'translate' 
          ? 'Whisper traduit vers l\'anglais, puis le LLM traduit en français (recommandé)' 
          : 'Whisper conserve la langue originale, puis le LLM traduit en français' }}
      </p>
    </div>

    <!-- LM Studio Port -->
    <div class="space-y-2">
      <label class="text-xs font-medium" :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'">Port LM Studio</label>
      <input
        v-model.number="lmStudioPort"
        type="number"
        min="1"
        max="65535"
        placeholder="7890"
        :class="[
          'w-full appearance-none rounded-notion px-3 py-2.5 text-sm transition-colors',
          'focus:outline-none focus:ring-1 focus:ring-notion-blue/20',
          isDark
            ? 'bg-[#2A2A2A] border border-[#444] text-[#E0E0E0] focus:border-notion-blue'
            : 'bg-white border border-notion-border text-notion-text focus:border-notion-blue',
        ]"
      />
      <p class="text-[11px]" :class="isDark ? 'text-[#666]' : 'text-notion-text-secondary'">
        Port par défaut : 7890. Modifiez si vous avez changé le port dans LM Studio.
      </p>
    </div>

    <!-- Translation Pre-prompt (optional) -->
    <div class="space-y-2">
      <label class="text-xs font-medium" :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'">
        Préprompt de traduction
        <span class="font-normal" :class="isDark ? 'text-[#555]' : 'text-notion-text-secondary'">(optionnel)</span>
      </label>
      <textarea
        v-model="translationPrompt"
        rows="3"
        placeholder="Ex: Utilise un ton familier, adapte les expressions idiomatiques..."
        :class="[
          'w-full appearance-none rounded-notion px-3 py-2.5 text-sm transition-colors resize-none',
          'focus:outline-none focus:ring-1 focus:ring-notion-blue/20',
          isDark
            ? 'bg-[#2A2A2A] border border-[#444] text-[#E0E0E0] placeholder-[#555] focus:border-notion-blue'
            : 'bg-white border border-notion-border text-notion-text placeholder-gray-300 focus:border-notion-blue',
        ]"
      ></textarea>
      <p class="text-[11px]" :class="isDark ? 'text-[#666]' : 'text-notion-text-secondary'">
        Instructions supplémentaires pour guider la traduction du LLM.
      </p>
    </div>

    <!-- LLM Model Selection -->
    <div class="space-y-2">
      <div class="flex items-center justify-between">
        <label class="text-xs font-medium" :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'">Modèle LLM (LM Studio)</label>
        <button
          @click="refreshLlmModels"
          :disabled="isLoadingLlm"
          class="text-[11px] text-notion-blue hover:text-notion-blue-hover transition-colors disabled:opacity-50"
        >
          {{ isLoadingLlm ? 'Chargement...' : 'Actualiser' }}
        </button>
      </div>

      <!-- Connection status -->
      <div v-if="!lmStudioConnected" class="flex items-center gap-2 p-3 rounded-notion border"
        :class="isDark ? 'bg-red-900/20 border-red-800/40' : 'bg-red-50 border-red-100'">
        <svg class="w-4 h-4 text-notion-red flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
        <p class="text-xs text-notion-red">
          LM Studio non détecté. Lancez LM Studio avec le serveur local activé.
        </p>
      </div>

      <div v-else class="relative">
        <select
          v-model="selectedLlmModel"
          :class="[
            'w-full appearance-none rounded-notion px-3 py-2.5 text-sm transition-colors cursor-pointer',
            'focus:outline-none focus:ring-1 focus:ring-notion-blue/20',
            isDark
              ? 'bg-[#2A2A2A] border border-[#444] text-[#E0E0E0] focus:border-notion-blue'
              : 'bg-white border border-notion-border text-notion-text focus:border-notion-blue',
          ]"
        >
          <option v-for="model in llmModels" :key="model.id" :value="model.id">
            {{ model.id }}
          </option>
        </select>
        <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none" :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </div>

      <div v-if="lmStudioConnected" class="flex items-center gap-1.5">
        <span class="w-1.5 h-1.5 rounded-full bg-notion-green"></span>
        <span class="text-[11px]" :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'">LM Studio connecté</span>
      </div>
    </div>

    <!-- Device info -->
    <div v-if="deviceInfo" class="flex items-center gap-2 pt-2 border-t" :class="isDark ? 'border-[#333]' : 'border-notion-border'">
      <svg class="w-3.5 h-3.5" :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
      <span class="text-[11px]" :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'">
        Accélération : <span class="font-medium">{{ deviceLabel }}</span>
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { getWhisperModels, getLlmModels, getDeviceInfo } from '../services/api.js'

const props = defineProps({ isDark: Boolean })
const emit = defineEmits(['config-changed'])

const selectedWhisperModel = ref('base')
const selectedLlmModel = ref('')
const selectedTask = ref('translate')
const lmStudioPort = ref(7890)
const translationPrompt = ref('')
const whisperModels = ref(['base', 'small', 'medium', 'large-v3'])
const llmModels = ref([])
const lmStudioConnected = ref(false)
const isLoadingLlm = ref(false)
const deviceInfo = ref(null)

const taskOptions = [
  { label: 'Via anglais (recommandé)', value: 'translate' },
  { label: 'Direct', value: 'transcribe' },
]

const modelLabels = {
  'base': 'Base — Rapide',
  'small': 'Small — Équilibré',
  'medium': 'Medium — Précis',
  'large-v3': 'Large-v3 — Maximum',
}

const modelDescriptions = {
  'base': '~1 Go VRAM — Rapide, moins précis. Idéal pour des tests.',
  'small': '~2 Go VRAM — Bon compromis vitesse/précision.',
  'medium': '~5 Go VRAM — Haute précision recommandée.',
  'large-v3': '~10 Go VRAM — Précision maximale. Nécessite un GPU puissant.',
}

const deviceLabel = computed(() => {
  if (!deviceInfo.value) return ''
  const d = deviceInfo.value.device
  const labels = {
    'cuda': 'NVIDIA CUDA GPU',
    'mps': 'Apple Silicon (MPS)',
    'cpu': 'CPU (lent)',
    'auto': 'Auto-détecté',
  }
  return labels[d] || d
})

// Emit config when anything changes
watch([selectedWhisperModel, selectedLlmModel, selectedTask, lmStudioPort, translationPrompt], () => {
  emit('config-changed', {
    whisperModel: selectedWhisperModel.value,
    llmModel: selectedLlmModel.value,
    whisperTask: selectedTask.value,
    lmStudioPort: lmStudioPort.value,
    translationPrompt: translationPrompt.value,
  })
})

async function refreshLlmModels() {
  isLoadingLlm.value = true
  try {
    const data = await getLlmModels(lmStudioPort.value)
    llmModels.value = data.models || []
    lmStudioConnected.value = data.connected
    if (llmModels.value.length > 0 && !selectedLlmModel.value) {
      selectedLlmModel.value = llmModels.value[0].id
    }
  } catch (e) {
    lmStudioConnected.value = false
    llmModels.value = []
  } finally {
    isLoadingLlm.value = false
  }
}

onMounted(async () => {
  // Load whisper models
  try {
    const data = await getWhisperModels()
    whisperModels.value = data.models
    selectedWhisperModel.value = data.default
  } catch (e) { /* keep defaults */ }

  // Load LLM models
  await refreshLlmModels()

  // Load device info
  try {
    deviceInfo.value = await getDeviceInfo()
  } catch (e) { /* ignore */ }
})
</script>