import { createApp } from 'vue'
import App from './App.vue'
import './style.css'
import { fr } from './locales/fr.js'

document.title = fr.app.title

createApp(App).mount('#app')
