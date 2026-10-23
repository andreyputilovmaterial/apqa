import CmdletChain from './cmdlet_chain';
import Comparison from './comparison';

// Compact QC-rule representation: one description line (name + optional
// comment) and one definition line (left chain, comparison op, right chain).
// Reuses the same `CmdletChain` and `Comparison` building blocks as the full
// `rule.js`, only the surrounding layout differs.
//
// The description line is the rule's "header": clicking it emits `toggle` so a
// wrapping record component can expand/collapse the rule.
const RuleCompact = {
  props: ['record'],

  emits: ['toggle'],

  components: {
    'cmdlet-chain': CmdletChain,
    'comparison': Comparison,
  },

  template: `
<div class="apqa-rule-compact">
  <div
    class="apqa-rule-compact-description"
    role="button"
    tabindex="0"
    @click="$emit('toggle')"
    @keydown.enter.prevent="$emit('toggle')"
  >
    <span class="apqa-rule-compact-name">{{ record.name }}</span>
    <span v-if="record.comment" class="apqa-rule-compact-comment">{{ record.comment }}</span>
  </div>
  <div class="apqa-rule-compact-definition">
    <cmdlet-chain :chain="record.left" />
    <comparison :op="record.op" />
    <cmdlet-chain :chain="record.right" />
  </div>
</div>
`,
};

export default RuleCompact;
