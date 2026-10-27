import { ref } from 'vue';

import InputCmdletChain from '@/common_components/input_cmdlet_chain/index';
import InputComparisonOp from '@/common_components/input_comparison_op/index';
import InputQcruleTags from '@/common_components/input_qcrule_tags/index';
import InputQcruleMarks from '@/common_components/input_qcrule_marks/index';

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
    'input-cmdlet-chain': InputCmdletChain,
    'input-comparison-op': InputComparisonOp,
    'input-qcrule-tags': InputQcruleTags,
    'input-qcrule-marks': InputQcruleMarks,
  },

  template: `
<div class="apqa-rule-edit-form apqa-rule-form">
  <form class="apqa-rule-form-inner" @submit.prevent="submit">
    <div v-if="error" class="apqa-rule-form-error">{{ error }}</div>

    <div class="apqa-rule-form-fields">
      <label class="apqa-rule-form-field">
        <span class="apqa-rule-form-field-label">Name <span class="apqa-rule-form-required">*</span></span>
        <input type="text" class="apqa-rule-form-input" name="name" v-model="name" />
      </label>

      <label class="apqa-rule-form-field">
        <span class="apqa-rule-form-field-label">Technical name (id)</span>
        <input type="text" class="apqa-rule-form-input apqa-rule-form-input-disabled" name="id" :value="record.id" disabled />
        <span class="apqa-rule-form-field-help">The technical id cannot be changed.</span>
      </label>

      <label class="apqa-rule-form-field">
        <span class="apqa-rule-form-field-label">Comment</span>
        <input type="text" class="apqa-rule-form-input" name="comment" v-model="comment" />
      </label>

      <label class="apqa-rule-form-field">
        <span class="apqa-rule-form-field-label">Tags</span>
        <input-qcrule-tags v-model="tags" :suggestions="tagSuggestions" />
      </label>

      <label class="apqa-rule-form-field">
        <span class="apqa-rule-form-field-label">Markers</span>
        <input-qcrule-marks v-model="markers" />
      </label>

      <label class="apqa-rule-form-field apqa-rule-form-field-chain">
        <span class="apqa-rule-form-field-label">Left side</span>
        <input-cmdlet-chain v-model="left" :cmdlets="cmdlets" />
      </label>

      <label class="apqa-rule-form-field">
        <span class="apqa-rule-form-field-label">Comparison</span>
        <input-comparison-op v-model="comparison" :ops="ops" />
      </label>

      <label class="apqa-rule-form-field apqa-rule-form-field-chain">
        <span class="apqa-rule-form-field-label">Right side</span>
        <input-cmdlet-chain v-model="right" :cmdlets="cmdlets" />
      </label>
    </div>

    <div class="apqa-rule-form-actions">
      <button type="button" class="apqa-rule-form-button" @click="cancel">Cancel</button>
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

    return {
      name,
      comment,
      tags,
      markers,
      left,
      right,
      comparison,
      error,
      submit,
      cancel,
    };
  },
};

export default RuleEditForm;
