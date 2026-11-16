import { ref } from 'vue';

import InputQcruleTags from '@/common_components/input_types/qcrules/tags/index';
import InputQcruleMarks from '@/common_components/input_types/qcrules/marks/index';

import './rule_form.css';
import './rule_edit_form.css';

// Inline form for editing an existing QC rule. It reuses the create-form field
// layout (`rule_form.css`), but is embedded inside the rule's own container
// instead of a modal. It is pre-filled from `record` and, on save, emits only
// the fields the user can change here; the page merges them back into the rule
// while preserving the rest of its meta (order, timestamps, unknown keys).
//
// The technical id is shown read-only because the backend treats it as stable
// (`PUT /qc/rules/<id>` refuses an `id` change).
const RuleEditForm = {
  props: {
    record: { type: Object, required: true },
    cmdlets: { type: Array, default: () => [] },
    ops: { type: Array, default: () => [] },
    tagSuggestions: { type: Array, default: () => [] },
  },

  emits: ['save', 'cancel'],

  components: {
    'input-qcrule-tags': InputQcruleTags,
    'input-qcrule-marks': InputQcruleMarks,
  },

  template: `
<div class="apqa-qcrules-entry apqa-qcrules-entry-rule apqa-rule-card apqa-rule-edit-form apqa-rule-form">
  <div class="apqa-rule-card-head">
    <span class="apqa-rule-card-name">{{ name }}</span>
    <span v-if="comment" class="apqa-rule-card-comment">{{ comment }}</span>
  </div>

  <div class="apqa-record-actions">
    <button type="button" class="apqa-record-action apqa-record-action-save" title="Save" aria-label="Save rule" @click="submit">
      <i class="ri-save-3-line" aria-hidden="true"></i>
    </button>
    <button type="button" class="apqa-record-action apqa-record-action-cancel" title="Close" aria-label="Close editing" @click="cancel">
      <i class="ri-close-circle-line" aria-hidden="true"></i>
    </button>
  </div>

  <form class="apqa-rule-form-inner" @submit.prevent="submit">
    <div v-if="error" class="apqa-rule-form-error">{{ error }}</div>

    <div class="apqa-rule-form-fields">
      <div class="apqa-rule-form-section">
        <div class="apqa-rule-form-field apqa-rule-form-id">
          <button
            type="button"
            class="apqa-rule-form-id-toggle"
            :aria-expanded="idExpanded ? 'true' : 'false'"
            @click="toggleId"
          >
            <i
              :class="idExpanded ? 'ri-arrow-up-double-fill' : 'ri-arrow-down-double-fill'"
              class="apqa-rule-form-id-icon"
              aria-hidden="true"
            ></i>
            <span class="apqa-rule-form-id-value">{{ record.id }}</span>
          </button>

          <label v-if="idExpanded" class="apqa-rule-form-id-editor">
            <span class="apqa-rule-form-field-label">QC rule ID</span>
            <input type="text" class="apqa-rule-form-input apqa-rule-form-input-disabled" name="id" :value="record.id" disabled />
            <span class="apqa-rule-form-field-help">The QC rule ID cannot be changed.</span>
          </label>
        </div>

        <label class="apqa-rule-form-field">
          <span class="apqa-rule-form-field-label">Name <span class="apqa-rule-form-required">*</span></span>
          <input type="text" class="apqa-rule-form-input" name="name" v-model="name" />
        </label>

        <label class="apqa-rule-form-field">
          <span class="apqa-rule-form-field-label">Comment</span>
          <input type="text" class="apqa-rule-form-input" name="comment" v-model="comment" />
        </label>
      </div>

      <div class="apqa-rule-form-section">
        <label class="apqa-rule-form-field apqa-rule-form-field-chain">
          <span class="apqa-rule-form-field-label">Left side</span>
          <component-input-cmdlet-chain v-model="left" :cmdlets="cmdlets" />
        </label>

        <label class="apqa-rule-form-field">
          <span class="apqa-rule-form-field-label">Comparison</span>
          <component-input-comparison-op v-model="comparison" :ops="ops" />
        </label>

        <label class="apqa-rule-form-field apqa-rule-form-field-chain">
          <span class="apqa-rule-form-field-label">Right side</span>
          <component-input-cmdlet-chain v-model="right" :cmdlets="cmdlets" />
        </label>
      </div>

      <div class="apqa-rule-form-section">
        <label class="apqa-rule-form-field">
          <span class="apqa-rule-form-field-label">Tags</span>
          <input-qcrule-tags v-model="tags" :suggestions="tagSuggestions" />
        </label>

        <label class="apqa-rule-form-field">
          <span class="apqa-rule-form-field-label">Markers</span>
          <input-qcrule-marks v-model="markers" />
        </label>
      </div>
    </div>

    <div class="apqa-rule-form-actions">
      <button type="button" class="apqa-rule-form-button" @click="cancel">Close</button>
      <button type="submit" class="apqa-rule-form-button apqa-rule-form-button-primary">Save</button>
    </div>
  </form>
</div>
`,

  setup(props, { emit }) {
    const record = props.record || {};

    const name = ref(record.name || '');
    const comment = ref(record.comment || '');
    const tags = ref(Array.isArray(record.tags) ? record.tags.slice() : []);
    const markers = ref(Array.isArray(record.markers) ? record.markers.slice() : []);
    const left = ref(Array.isArray(record.left) ? record.left.slice() : []);
    const right = ref(Array.isArray(record.right) ? record.right.slice() : []);
    const comparison = ref(
      record.op
        ? { op: record.op, op_args: { ...(record.op_args || {}) } }
        : null,
    );
    const error = ref('');
    const idExpanded = ref(false);

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
        left: left.value || [],
        op: comparison.value?.op || '',
        op_args: comparison.value?.op_args || {},
        right: right.value || [],
      });
    }

    function cancel() {
      emit('cancel');
    }

    function toggleId() {
      idExpanded.value = !idExpanded.value;
    }

    return {
      name,
      comment,
      tags,
      markers,
      left,
      right,
      comparison,
      error,
      idExpanded,
      toggleId,
      submit,
      cancel,
    };
  },
};

export default RuleEditForm;
