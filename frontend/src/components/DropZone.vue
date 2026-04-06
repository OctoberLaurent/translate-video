<template>
  <div
    @dragover.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
    @drop.prevent="handleDrop"
    @click="triggerFileInput"
    :class="[
      'relative flex flex-col items-center justify-center w-full min-h-[200px]',
      'border-2 border-dashed rounded-notion cursor-pointer',
      'transition-all duration-200 ease-in-out',
      isDragging
        ? 'border-notion-blue ' + (isDark ? 'bg-notion-blue/10' : 'bg-notion-blue-bg/50')
        : (file || initialFileName)
          ? 'border-notion-green ' + (isDark ? 'bg-green-900/20' : 'bg-green-50/50')
          : isDark
            ? 'border-[#444] hover:border-notion-blue hover:bg-[#2A2A2A]'
            : 'border-notion-border hover:border-notion-blue hover:bg-notion-hover',
    ]"
  >
    <input
      ref="fileInput"
      type="file"
      :accept="acceptedExtensions"
      @change="handleFileSelect"
      class="hidden"
    />

    <!-- Upload icon & text (no file, no restored name) -->
    <div v-if="!file && !initialFileName" class="flex flex-col items-center gap-3 py-8">
      <svg :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'" class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
      <div class="text-center">
        <p class="text-sm font-medium" :class="isDark ? 'text-[#E0E0E0]' : 'text-notion-text'">
          Glissez votre vidéo ici
        </p>
        <p class="text-xs mt-1" :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'">
          ou cliquez pour sélectionner
        </p>
      </div>
      <div class="flex gap-1 mt-2">
        <span v-for="ext in ['MP4', 'MKV', 'AVI', 'MOV']" :key="ext"
          :class="isDark ? 'bg-[#333] text-[#888]' : 'bg-notion-hover text-notion-text-secondary'"
          class="text-[10px] px-1.5 py-0.5 rounded">
          {{ ext }}
        </span>
      </div>
    </div>

    <!-- File selected or restored -->
    <div v-else class="flex items-center gap-4 py-6 px-8 w-full">
      <div :class="isDark ? 'bg-notion-blue/20' : 'bg-notion-blue-bg'" class="flex-shrink-0 w-10 h-10 rounded-notion flex items-center justify-center">
        <svg :class="isDark ? 'text-blue-400' : 'text-notion-blue'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      </div>
      <div class="flex-1 min-w-0">
        <p class="text-sm font-medium truncate" :class="isDark ? 'text-[#E0E0E0]' : 'text-notion-text'">{{ displayName }}</p>
        <p v-if="file" class="text-xs mt-0.5" :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'">{{ formatFileSize(file.size) }}</p>
        <p v-else class="text-xs mt-0.5" :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'">
          <span class="flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full bg-notion-green"></span>
            Fichier déjà uploadé (session précédente)
          </span>
        </p>
      </div>
      <button
        @click.stop="removeFile"
        :class="isDark ? 'hover:bg-[#333]' : 'hover:bg-notion-hover'"
        class="flex-shrink-0 p-1.5 rounded transition-colors"
      >
        <svg :class="isDark ? 'text-[#888]' : 'text-notion-text-secondary'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({ 
  isDark: Boolean, 
  initialFileName: { type: String, default: '' }
})
const emit = defineEmits(['file-selected', 'file-removed'])

const file = ref(null)
const isDragging = ref(false)
const fileInput = ref(null)

// Show restored file name if no actual file but initialFileName is set
const displayName = computed(() => {
  if (file.value) return file.value.name
  if (props.initialFileName) return props.initialFileName
  return ''
})

const acceptedExtensions = computed(() => '.mp4,.mkv,.avi,.mov,.wmv,.flv,.webm')

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileSelect(event) {
  const selected = event.target.files?.[0]
  if (selected) {
    file.value = selected
    emit('file-selected', selected)
  }
}

function handleDrop(event) {
  isDragging.value = false
  const dropped = event.dataTransfer?.files?.[0]
  if (dropped) {
    file.value = dropped
    emit('file-selected', dropped)
  }
}

function removeFile() {
  file.value = null
  if (fileInput.value) fileInput.value.value = ''
  emit('file-removed')
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}
</script>