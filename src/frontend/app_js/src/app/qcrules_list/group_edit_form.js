import { ref } from 'vue';

import InputQcruleTags from '@/common_components/input_types/qcrules/tags/index';
import InputQcruleMarks from '@/common_components/input_types/qcrules/marks/index';

import './group_form.css';
import './group_edit_form.css';

// Inline form for editing an existing folder (group). It mirrors the rule edit
// form's layout: the same folder header + an icon action row on top, then the
// editable fields, then full-size Save/Close buttons. The technical id is stable
// (the backend refuses an id change), so it is not exposed here. On save it emits
// only the fields the user can change; the page merges them back into the group.
const GroupEditForm = {
  props: {
    group: { type: Object, required: true },
    collapsed: { type: Boolean, default: false },
    tagSuggestions: { type: Array, default: () => [] },
  },

  emits: ['save', 'cancel'],

  components: {
    'input-qcrule-tags': InputQcruleTags,
    'input-qcrule-marks': InputQcruleMarks,
  },

  template: `
<div class="apqa-qcrules-entry apqa-qcrules-entry-folder apqa-rules-tree-group-card apqa-group-edit-form">
  <div class="apqa-rules-tree-group-header">
    <span class="apqa-rules-tree-group-header-row">
      <span class="apqa-rules-tree-group-toggle" aria-hidden="true">{{ collapsed ? '[+]' : '[-]' }}</span>
      <span class="apqa-rules-tree-group-name">{{ name }}</span>
    </span>
    <span v-if="comment" class="apqa-rules-tree-group-comment">{{ comment }}</span>
  </div>

  <div class="apqa-record-actions">
    <button type="button" class="apqa-record-action apqa-record-action-save" title="Save" aria-label="Save folder" @click="submit">
      <i class="ri-save-3-line" aria-hidden="true"></i>
    </button>
    <button type="button" class="apqa-record-action apqa-record-action-cancel" title="Close" aria-label="Close editing" @click="cancel">
      <i class="ri-close-circle-line" aria-hidden="true"></i>
    </button>
  </div>

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

      <div class="apqa-group-form-section">
        <label class="apqa-group-form-field">
          <span class="apqa-group-form-field-label">Tags</span>
          <input-qcrule-tags v-model="tags" :suggestions="tagSuggestions" />
        </label>

        <label class="apqa-group-form-field">
          <span class="apqa-group-form-field-label">Markers</span>
          <input-qcrule-marks v-model="markers" />
        </label>
      </div>
    </div>

    <div class="apqa-group-form-actions">
      <button type="button" class="apqa-group-form-button" @click="cancel">Close</button>
      <button type="submit" class="apqa-group-form-button apqa-group-form-button-primary">Save</button>
    </div>
  </form>
</div>
`,

  setup(props, { emit }) {
    const group = props.group || {};

    const name = ref(group.name || '');
    const comment = ref(group.comment || '');
    const tags = ref(Array.isArray(group.tags) ? group.tags.slice() : []);
    const markers = ref(Array.isArray(group.markers) ? group.markers.slice() : []);
    const error = ref('');

    function submit() {
      const trimmedName = name.value.trim();
      if (!trimmedName) {
        error.value = 'Name is required.';
        return;
      }
      error.value = '';

      emit('save', {
        name: trimmedName,
        comment: comment.value.trim(),
        tags: tags.value.slice(),
        markers: markers.value.slice(),
      });
    }

    function cancel() {
      emit('cancel');
    }

    return { name, comment, tags, markers, error, submit, cancel };
  },
};

export default GroupEditForm;
