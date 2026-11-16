import { ref } from 'vue';

import './group_form.css';

// Modal form for creating a folder (group): a name and an optional
// description/comment, mirroring the rule form's name + comment fields. New
// folders are always created at the top level (`parent: ''`); nesting a folder
// under another is a separate, later flow. On submit it builds the payload and
// resolves the surrounding modal promise with it (the page then POSTs and
// reloads).
const GroupForm = {
  props: ['resolve', 'reject'],

  template: `
<div class="apqa-modal-form apqa-group-form">
  <form class="apqa-group-form-inner" @submit.prevent="submit">
    <div v-if="error" class="apqa-group-form-error">{{ error }}</div>

    <div class="apqa-group-form-fields">
      <div class="apqa-group-form-section">
        <label class="apqa-group-form-field">
          <span class="apqa-group-form-field-label">Name <span class="apqa-group-form-required">*</span></span>
          <input type="text" class="apqa-group-form-input" name="name" v-model="name" />
        </label>

        <label class="apqa-group-form-field">
          <span class="apqa-group-form-field-label">Comment</span>
          <input type="text" class="apqa-group-form-input" name="comment" v-model="comment" />
        </label>
      </div>
    </div>

    <div class="apqa-modal-actions">
      <button type="submit" class="apqa-button-close apqa-button-primary">Create folder</button>
      <button type="button" class="apqa-button-close" @click="cancel">Cancel</button>
    </div>
  </form>
</div>
`,

  setup(props) {
    const name = ref('');
    const comment = ref('');
    const error = ref('');

    function submit() {
      const trimmedName = name.value.trim();
      if (!trimmedName) {
        error.value = 'Name is required.';
        return;
      }
      error.value = '';

      const meta = {};
      if (comment.value.trim()) meta.comment = comment.value.trim();

      const payload = {
        name: trimmedName,
        parent: '',
      };
      if (Object.keys(meta).length) payload.meta = meta;

      props.resolve(payload);
    }

    function cancel() {
      props.reject();
    }

    return { name, comment, error, submit, cancel };
  },
};

export default GroupForm;
