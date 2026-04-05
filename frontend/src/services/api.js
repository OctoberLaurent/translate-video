/**
 * API service for communicating with the SubTranslate backend.
 */

const API_BASE = '/api'

/**
 * Upload a video file to the backend.
 * @param {File} file - The video file to upload.
 * @returns {Promise<Object>} Upload response with file info.
 */
export async function uploadVideo(file) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Erreur lors de l\'upload')
  }

  return response.json()
}

/**
 * Get available Whisper model sizes.
 * @returns {Promise<Object>} Object with models list and default.
 */
export async function getWhisperModels() {
  const response = await fetch(`${API_BASE}/whisper-models`)
  return response.json()
}

/**
 * Get available LLM models from LM Studio.
 * @returns {Promise<Object>} Object with models list and connection status.
 */
export async function getLlmModels(port = null) {
  const url = port ? `${API_BASE}/llm-models?port=${port}` : `${API_BASE}/llm-models`
  const response = await fetch(url)
  return response.json()
}

/**
 * Get detected compute device info.
 * @returns {Promise<Object>} Device info.
 */
export async function getDeviceInfo() {
  const response = await fetch(`${API_BASE}/device`)
  return response.json()
}

/**
 * Check backend health.
 * @returns {Promise<Object>} Health status.
 */
export async function healthCheck() {
  const response = await fetch(`${API_BASE}/health`)
  return response.json()
}

/**
 * Get the download URL for an SRT file.
 * @param {string} filename - SRT filename.
 * @returns {string} Download URL.
 */
export function getDownloadUrl(filename) {
  return `${API_BASE}/download/${encodeURIComponent(filename)}`
}

/**
 * Download an SRT file as a Blob via fetch.
 * @param {string} filename - SRT filename.
 * @returns {Promise<{blob: Blob, filename: string}>} Downloaded file as Blob.
 * @throws {Error} If the backend is unreachable or returns an error.
 */
export async function downloadSrtFile(filename) {
  const url = getDownloadUrl(filename)

  const response = await fetch(url)

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Fichier SRT introuvable sur le serveur.')
    }
    const errorData = await response.json().catch(() => null)
    throw new Error(errorData?.detail || `Erreur serveur (${response.status})`)
  }

  const blob = await response.blob()

  // Extract filename from Content-Disposition header if available
  const disposition = response.headers.get('Content-Disposition')
  let downloadName = filename
  if (disposition) {
    const match = disposition.match(/filename="?([^"]+)"?/)
    if (match) downloadName = match[1]
  }

  return { blob, filename: downloadName }
}

/**
 * Create a WebSocket connection for the pipeline.
 * @param {string} wsUrl - WebSocket URL.
 * @returns {WebSocket} WebSocket instance.
 */
export function createPipelineWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  return new WebSocket(`${protocol}//${host}/api/ws/pipeline`)
}