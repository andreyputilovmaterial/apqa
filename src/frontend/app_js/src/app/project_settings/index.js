import { ref, onMounted } from 'vue';

import { makeFetchResponseErrorMessage } from '@/common_defs/helper_functions';
import logError from '@/common_components/_log_error_proxy';
import { fetchProjectInfo, applyProjectHeaderInfo } from './project_header';

import './styles.css';

// Modal opened from the gear icon in the page header. It edits the project-level
// metadata (name + description/comment) stored in the rules database file and
// exposed through `GET`/`PUT /qc/project`. On save it re-reads the project and
// updates the header + page title in place, so it works the same in the Vite dev
// server and the backend-served bundle without a full page reload.
const ProjectSettingsModal = {
  props: ['resolve', 'reject'],

  template: `
<div class="apqa-modal-form apqa-project-settings-form">
  <div class="apqa-project-settings-form-header">
    <h2 class="apqa-project-settings-form-title">Project</h2>
    <p class="apqa-modal-form-subtitle apqa-project-settings-form-subtitle">Project name and description shown in the page header.</p>
  </div>

  <form class="apqa-project-settings-form-inner" @submit.prevent="save">
    <div v-if="error" class="apqa-project-settings-form-error">{{ error }}</div>
    <div v-if="loading" class="apqa-project-settings-form-loading">Loading project…</div>

    <template v-else>
      <label class="apqa-project-settings-form-field">
        <span class="apqa-project-settings-form-field-label">Project name</span>
        <input type="text" class="apqa-project-settings-form-input" v-model="name" />
      </label>

      <label class="apqa-project-settings-form-field">
        <span class="apqa-project-settings-form-field-label">Description</span>
        <textarea class="apqa-project-settings-form-input apqa-project-settings-form-textarea" v-model="comment" rows="3"></textarea>
      </label>
    </template>

    <div class="apqa-modal-actions">
      <button type="submit" class="apqa-button-close apqa-button-primary" :disabled="saving || loading">{{ saving ? 'Saving…' : 'Save' }}</button>
      <button type="button" class="apqa-button-close" @click="close" :disabled="saving">Cancel</button>
    </div>
  </form>
</div>
`,

  setup(props) {
    const name = ref('');
    const comment = ref('');
    const loading = ref(true);
    const saving = ref(false);
    const error = ref('');

    async function load() {
      loading.value = true;
      error.value = '';
      try {
        const project = (await fetchProjectInfo()).project || {};
        name.value = project.name || '';
        comment.value = project.comment || '';
      } catch (e) {
        error.value = `Failed to load project: ${e}`;
        logError(error.value);
      } finally {
        loading.value = false;
      }
    }

    async function save() {
      saving.value = true;
      error.value = '';
      try {
        const response = await fetch('/qc/project', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: name.value.trim(),
            comment: comment.value.trim(),
          }),
        });
        if (!response.ok) {
          throw new Error(await makeFetchResponseErrorMessage(response));
        }
        // Re-read the persisted project (including the database path) and update
        // the header + page title in place, then close the modal.
        applyProjectHeaderInfo(await fetchProjectInfo());
        props.resolve();
      } catch (e) {
        error.value = `Failed to save project: ${e}`;
        logError(error.value);
        saving.value = false;
      }
    }

    function close() {
      props.reject();
    }

    onMounted(load);

    return { name, comment, loading, saving, error, save, close };
  },
};

export default ProjectSettingsModal;
