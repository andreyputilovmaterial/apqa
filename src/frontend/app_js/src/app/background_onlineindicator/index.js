

import './styles.css';

import { ref, onMounted, onUnmounted } from 'vue';

// Project path is served in the header (server-rendered in the bundle; filled in
// by the project-header populator in the Vite dev server). It is the project the
// frontend was loaded against, i.e. the value a path change is compared to.
const PROJECT_PATH_SELECTOR = '.apqaui-html-page-project-path';
const HEALTH_URL = '/health';
const PROJECT_URL = '/qc/project';
const POLL_INTERVAL_MS = 5000;

// Full-screen overlay that shouts out loudly when the backend can no longer be
// trusted to be serving the project this page was loaded for:
//   - grey "Backend is offline" panel when /health no longer answers 200
//   - red "project file has changed" panel (with a reload link) when the path
//     returned by GET /qc/project differs from the path captured on load.
// Mirrors the look of gitgui's background_onlineindicator.
const OnlineMonitor = {
  template: `
<div
  class="apqa-online-monitor"
  :class="{ 'online': isOnline && !projectPathChanged }"
  role="alert"
  aria-live="assertive"
>
  <div class="description" v-if="!isOnline && !projectPathChanged">
    Backend is offline or not responding, please check if the app is still running...
  </div>
  <div class="config-paths-mismatch-failure error" v-if="projectPathChanged">
    <span class="desc-line">
      The project file has changed. This page was loaded for:</span>
    <br />
    <br />
    <code>{{ initialProjectPath }}</code>
    <br />
    <br />
    <span class="desc-line">
      The backend is now serving: <code>{{ currentProjectPath }}</code></span>
    <br />
    <br />
    <span class="suggest-line">
      Please <a href="" @click.prevent="reloadPage" class="mdm-link-btn">reload the page</a>
    </span>
  </div>
</div>
`,
  setup() {
    const isOnline = ref(true);
    const projectPathChanged = ref(false);
    const initialProjectPath = ref('');
    const currentProjectPath = ref('');

    let timer = null;
    let inFlight = false;

    function reloadPage() {
      window.location.reload();
    }

    function captureInitialPathFromDom() {
      const el = document.querySelector(PROJECT_PATH_SELECTOR);
      const text = el && el.textContent ? el.textContent.trim() : '';
      if (text) {
        initialProjectPath.value = text;
      }
    }

    async function pollOnce() {
      if (inFlight) return;
      inFlight = true;
      try {
        // Liveness: /health answers 200 to HEAD while the backend is up.
        try {
          const response = await fetch(HEALTH_URL, { method: 'HEAD' });
          isOnline.value = response.ok;
        } catch {
          isOnline.value = false;
        }

        // Project identity: compare the path served by the backend to the one
        // captured when the page was loaded.
        try {
          const response = await fetch(PROJECT_URL);
          if (!response.ok) return;
          const payload = await response.json();
          const path = (payload && payload.path) ? payload.path : '';
          if (!path) return;
          if (!initialProjectPath.value) {
            // Vite dev server: the header path is empty at mount, so capture the
            // authoritative path from the first successful project fetch.
            initialProjectPath.value = path;
          }
          currentProjectPath.value = path;
          projectPathChanged.value = (
            currentProjectPath.value !== initialProjectPath.value
          );
        } catch {
          // A failing project fetch while /health also fails is already covered
          // by the grey offline panel; nothing to flag here.
        }
      } finally {
        inFlight = false;
      }
    }

    onMounted(() => {
      captureInitialPathFromDom();
      pollOnce();
      timer = setInterval(pollOnce, POLL_INTERVAL_MS);
    });

    onUnmounted(() => {
      if (timer) clearInterval(timer);
      timer = null;
    });

    return {
      isOnline,
      projectPathChanged,
      initialProjectPath,
      currentProjectPath,
      reloadPage,
    };
  },
};

export default OnlineMonitor;
