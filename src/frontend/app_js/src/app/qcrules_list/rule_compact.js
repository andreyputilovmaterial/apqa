import { computed } from 'vue';

import MarksBadges, { INVALID_MESSAGE, UNFINISHED_MESSAGE } from './marks_badges';
import { isInvalid, isUnfinished, markNamesForRecord } from './grouping';

// Compact QC-rule representation: one description line (name + optional
// comment) and one definition line (left chain, comparison op, right chain).
// Reuses the same display `cmdlet-chain` / `comparison-op` building blocks as
// the full `rule.js`, only the form (compact vs full) and surrounding layout
// differ.
//
// The description line is the rule's "header": clicking it emits `toggle` so a
// wrapping record component can expand/collapse the rule. A grey helper note
// under the name explains each derived mark (`unfinished`/`invalid`), and a
// final line lists short mark badges.
const RuleCompact = {
  props: ['record', 'cmdlets', 'ops'],

  emits: ['toggle'],

  components: {
    'marks-badges': MarksBadges,
  },

  template: `
<div class="apqa-qcrules-entry apqa-qcrules-entry-rule apqa-rule-compact">
  <div
    class="apqa-rule-compact-description"
    role="button"
    tabindex="0"
    @click="$emit('toggle')"
    @keydown.enter.prevent="$emit('toggle')"
  >
    <span class="apqa-rule-compact-name"><i class="ri-arrow-down-double-fill apqa-rule-expand-icon" aria-hidden="true"></i>{{ record.name }}</span>
    <span v-if="record.comment" class="apqa-rule-compact-comment">{{ record.comment }}</span>
    <span v-if="unfinished" class="apqa-rule-unfinished-note">{{ UNFINISHED_MESSAGE }}</span>
    <span v-if="invalid" class="apqa-rule-invalid-note">{{ INVALID_MESSAGE }}</span>
  </div>
  <div class="apqa-rule-compact-definition">
    <component-cmdlet-chain-compact :chain="record.left" :cmdlets="cmdlets" />
    <component-comparison-op-compact :op="record.op" :ops="ops" />
    <component-cmdlet-chain-compact :chain="record.right" :cmdlets="cmdlets" />
  </div>
  <marks-badges :marks="marks" />
</div>
`,

  setup(props) {
    const unfinished = computed(() => isUnfinished(props.record, props.cmdlets, props.ops));
    const invalid = computed(() => isInvalid(props.record, props.cmdlets, props.ops));
    const marks = computed(() => markNamesForRecord(props.record, props.cmdlets, props.ops));
    return { UNFINISHED_MESSAGE, INVALID_MESSAGE, unfinished, invalid, marks };
  },
};

export default RuleCompact;
