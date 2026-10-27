import { ref, watch } from 'vue';

import InputCmdletChain from '../../common_components/input_cmdlet_chain/index';
import InputComparisonOp from '../../common_components/input_comparison_op/index';
import InputQcruleTags from '../../common_components/input_qcrule_tags/index';
import InputQcruleMarks from '../../common_components/input_qcrule_marks/index';

import './rule_form.css';

// Mirror of `src/db_processors/ids.py:make_slug` so the technical id shown in
// the form matches what the backend would generate for the same display name.
export function makeSlug(text, fallback = 'rule') {
  const normalized = String(text ?? '')
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '');
  const parts = normalized.toLowerCase().match(/[a-z0-9]+/g) || [];
  let slug = parts.join('-');
  if (!slug) slug = fallback;
  else if (/^[0-9]/.test(slug)) slug = `${fallback}-${slug}`;
  return slug;
}

// Modal form for creating a QC rule: one input per rule field. New rules are
// always created at the top level (`group: ''`); moving a rule into a folder is
// a separate, later flow. On submit it builds the payload and resolves the
// surrounding modal promise with it (the page then POSTs and reloads).
const RuleForm = {
  props: ['resolve', 'reject', 'cmdlets', 'ops', 'tagSuggestions'],

  components: {
    'input-cmdlet-chain': InputCmdletChain,
    'input-comparison-op': InputComparisonOp,
    'input-qcrule-tags': InputQcruleTags,
    'input-qcrule-marks': InputQcruleMarks,
  },

  template: `
<div class="apqa-modal-form apqa-rule-form">
  <form class="apqa-rule-form-inner" @submit.prevent="submit">
    <div v-if="error" class="apqa-rule-form-error">{{ error }}</div>

    <div class="apqa-rule-form-fields">
      <label class="apqa-rule-form-field">
        <span class="apqa-rule-form-field-label">Technical name (id)</span>
        <input type="text" class="apqa-rule-form-input" name="id" :value="id" @input="onIdInput" />
        <span class="apqa-rule-form-field-help">Auto-filled from the name; editable.</span>
      </label>

      <label class="apqa-rule-form-field">
        <span class="apqa-rule-form-field-label">Name <span class="apqa-rule-form-required">*</span></span>
        <input type="text" class="apqa-rule-form-input" name="name" v-model="name" />
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
      <button type="submit" class="apqa-rule-form-button apqa-rule-form-button-primary">Create rule</button>
    </div>
  </form>
</div>
`,

  setup(props) {
    const name = ref('');
    const id = ref('');
    const idTouched = ref(false);
    const comment = ref('');
    const tags = ref([]);
    const markers = ref([]);
    const left = ref([]);
    const right = ref([]);
    const comparison = ref(null);
    const error = ref('');

    // Auto-fill the technical id from the display name until the user edits it.
    watch(name, (value) => {
      if (!idTouched.value) id.value = makeSlug(value);
    });

    function onIdInput(event) {
      idTouched.value = true;
      id.value = event.target.value;
    }

    function submit() {
      const trimmedName = name.value.trim();
      if (!trimmedName) {
        error.value = 'Name is required.';
        return;
      }

      const meta = {};
      if (comment.value.trim()) meta.comment = comment.value.trim();
      if (tags.value.length) meta.tags = tags.value.slice();
      if (markers.value.length) meta.markers = markers.value.slice();

      const payload = {
        name: trimmedName,
        group: '',
        left: left.value || [],
        op: comparison.value?.op || '',
        op_args: comparison.value?.op_args || {},
        right: right.value || [],
      };
      if (id.value) payload.id = id.value;
      if (Object.keys(meta).length) payload.meta = meta;

      props.resolve(payload);
    }

    function cancel() {
      props.reject();
    }

    return {
      name,
      id,
      comment,
      tags,
      markers,
      left,
      right,
      comparison,
      error,
      onIdInput,
      submit,
      cancel,
    };
  },
};

export default RuleForm;
