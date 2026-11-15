import { computed } from 'vue';

import Rule from './rule';
import RuleCompact from './rule_compact';
import RuleEditForm from './rule_edit_form';
import { formatNote } from './run_result';

// Inner wrapper of a rule record. When not editing it holds the rendered rule
// (compact or full, chosen by `expanded`) plus a row of action buttons
// (Edit/Run/Delete). When `editing` is true the rule display is replaced by the
// inline edit form, whose save/cancel are forwarded up with the record.
const RuleBody = {
  props: {
    record: { type: Object, required: true },
    expanded: { type: Boolean, default: false },
    editing: { type: Boolean, default: false },
    runResults: { type: Object, default: () => ({}) },
    cmdlets: { type: Array, default: () => [] },
    ops: { type: Array, default: () => [] },
    tagSuggestions: { type: Array, default: () => [] },
  },

  emits: ['toggle', 'edit', 'run', 'delete', 'save', 'cancel'],

  components: {
    'rule': Rule,
    'rule-compact': RuleCompact,
    'rule-edit-form': RuleEditForm,
  },

  template: `
<div class="apqa-rule-body">
  <rule-edit-form
    v-if="editing"
    :record="record"
    :cmdlets="cmdlets"
    :ops="ops"
    :tag-suggestions="tagSuggestions"
    @save="$emit('save', record, $event)"
    @cancel="$emit('cancel', record)"
  />
  <template v-else>
    <rule-compact v-if="!expanded" :record="record" :cmdlets="cmdlets" :ops="ops" @toggle="$emit('toggle')" />
    <rule v-else :record="record" :cmdlets="cmdlets" :ops="ops" @toggle="$emit('toggle')" />

    <div v-if="expanded && runResult" class="apqa-rule-run-result">
      <div v-if="runResult.status === 'running'" class="apqa-rule-run-result-status apqa-rule-run-result-running">Running...</div>
      <template v-else>
        <div v-if="runResult.status === 'error'" class="apqa-rule-run-result-error">{{ runResult.message }}</div>
        <div v-else class="apqa-rule-run-result-status" :class="runResult.status === 'passed' ? 'apqa-rule-run-result-passed' : 'apqa-rule-run-result-failed'">{{ runResult.status === 'passed' ? 'Passed' : 'Failed' }}</div>
        <ul v-if="runResult.status === 'failed' && runResult.notes && runResult.notes.length" class="apqa-rule-run-result-notes">
          <li v-for="(note, index) in runResult.notes" :key="index">- {{ formatNote(note) }}</li>
        </ul>
      </template>
    </div>

    <div v-if="expanded" class="apqa-rule-body-actions">
      <button type="button" class="apqa-rule-body-action apqa-rule-body-action-edit" @click="$emit('edit', record)">Edit</button>
      <button type="button" class="apqa-rule-body-action apqa-rule-body-action-run" @click="$emit('run', record)">Run</button>
      <button type="button" class="apqa-rule-body-action apqa-rule-body-action-delete" @click="$emit('delete', record)">Delete</button>
    </div>
  </template>
</div>
`,

  setup(props) {
    const runResult = computed(() => props.runResults[props.record.id] || null);
    return { runResult, formatNote };
  },
};

export default RuleBody;
