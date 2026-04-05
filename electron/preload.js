/**
 * SubTranslate — Electron Preload Script
 * 
 * Exposes a safe API to the renderer process via contextBridge.
 */
const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('subtranslate', {
  platform: process.platform,
  version: require('./package.json').version,
});