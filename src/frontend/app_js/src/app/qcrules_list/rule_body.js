import { computed } from 'vue';

import ComponentFormatDatetime from '@/common_components/display/format_datetime/index';
import MarksBadges, { INVALID_MESSAGE, UNFINISHED_MESSAGE } from './marks_badges';
import { isInvalid, isUnfinished, markNamesForRecord } from './grouping';
import RuleEditForm from './rule_edit_form';
import { formatNote } from './run_result';

// Renders one QC rule as a single, always-visible card. When `editing` is true
// the card is replaced by the inline edit form; otherwise it shows, in order:
//   1. name + optional comment (the rule header, which is also the reorder drag
//      surface),
//   2. an icon-only action row (Edit / Run / Delete),
//   3. the cached last-run result (only when one exists),
//   4. the rule content (left chain, comparison, right chain),
//   5. meta (tags, markers, created timestamp).
// Rules no longer expand/collapse — the whole card is always shown. (Folders in
// the rules tree keep their own [+]/[-] toggle.)
const RuleBody = {
  props: {
    record: { type: Object, required: true },
    editing: { type: Boolean, default: false },
    runResults: { type: Object, default: () => ({}) },
    cmdlets: { type: Array, default: () => [] },
    ops: { type: Array, default: () => [] },
    tagSuggestions: { type: Array, default: () => [] },
  },

  emits: ['edit', 'run', 'delete', 'save', 'cancel'],

  components: {
    'rule-edit-form': RuleEditForm,
    'component-format-datetime': ComponentFormatDatetime,
    'marks-badges': MarksBadges,
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
  <div v-else class="apqa-qcrules-entry apqa-qcrules-entry-rule apqa-rule-card">
    <div class="apqa-rule-card-head">
      <span class="apqa-rule-card-name">{{ record.name }}</span>
      <span v-if="record.comment" class="apqa-rule-card-comment">{{ record.comment }}</span>
      <span v-if="unfinished" class="apqa-rule-unfinished-note">{{ UNFINISHED_MESSAGE }}</span>
      <span v-if="invalid" class="apqa-rule-invalid-note">{{ INVALID_MESSAGE }}</span>
    </div>

    <div class="apqa-record-actions">
      <button type="button" class="apqa-record-action apqa-record-action-edit" title="Edit" aria-label="Edit rule" @click="$emit('edit', record)">
        <i class="ri-edit-box-line" aria-hidden="true"></i>
      </button>
      <button type="button" class="apqa-record-action apqa-record-action-run" title="Run" aria-label="Run rule" @click="$emit('run', record)">
        <i class="ri-play-large-line" aria-hidden="true"></i>
      </button>
      <button type="button" class="apqa-record-action apqa-record-action-delete" title="Delete" aria-label="Delete rule" @click="$emit('delete', record)">
        <i class="ri-delete-bin-6-line" aria-hidden="true"></i>
      </button>
    </div>

    <div v-if="runResult" class="apqa-rule-run-result">
      <div v-if="runResult.status === 'running'" class="apqa-rule-run-result-status apqa-rule-run-result-running">Running...</div>
      <template v-else>
        <div v-if="runResult.status === 'error'" class="apqa-rule-run-result-error">{{ runResult.message }}</div>
        <div v-else class="apqa-rule-run-result-status" :class="runResult.status === 'passed' ? 'apqa-rule-run-result-passed' : 'apqa-rule-run-result-failed'">{{ runResult.status === 'passed' ? 'Passed' : 'Failed' }}</div>
        <ul v-if="runResult.status === 'failed' && runResult.notes && runResult.notes.length" class="apqa-rule-run-result-notes">
          <li v-for="(note, index) in runResult.notes" :key="index">- {{ formatNote(note) }}</li>
        </ul>
      </template>
    </div>

    <div class="apqa-rule-card-definition">
      <component-cmdlet-chain-compact :chain="record.left" :cmdlets="cmdlets" />
      <component-comparison-op-compact :op="record.op" :ops="ops" />
      <component-cmdlet-chain-compact :chain="record.right" :cmdlets="cmdlets" />
    </div>

    <div v-if="(record.tags && record.tags.length) || marks.length || record.created_at" class="apqa-record-meta">
      <span v-if="record.tags && record.tags.length" class="apqa-record-tags">{{ record.tags.join(', ') }}</span>
      <marks-badges :marks="marks" />
      <span v-if="record.created_at" class="apqa-record-created">created <component-format-datetime :dt="record.created_at" /></span>
    </div>
  </div>
</div>
`,

  setup(props) {
    const runResult = computed(() => props.runResults[props.record.id] || null);
    const unfinished = computed(() => isUnfinished(props.record, props.cmdlets, props.ops));
    const invalid = computed(() => isInvalid(props.record, props.cmdlets, props.ops));
    const marks = computed(() => markNamesForRecord(props.record, props.cmdlets, props.ops));

    return { UNFINISHED_MESSAGE, INVALID_MESSAGE, runResult, unfinished, invalid, marks, formatNote };
  },
};

export default RuleBody;
