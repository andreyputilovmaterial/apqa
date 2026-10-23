import CmdletChain from './cmdlet_chain';
import Comparison from './comparison';

// Compact QC-rule representation: one description line (name + optional
// comment) and one definition line (left chain, comparison op, right chain).
// Reuses the same `CmdletChain` and `Comparison` building blocks as the full
// `rule.js`, only the surrounding layout differs.
const RuleCompact = {
  props: ['record'],

  components: {
    'cmdlet-chain': CmdletChain,
    'comparison': Comparison,
  },

  template: `
<li class="apqa-rule-compact" :class="record._filterMeta.cssClasses">
  <div class="apqa-rule-compact-description">
    <span class="apqa-rule-compact-name">{{ record.name }}</span>
    <span v-if="record.comment" class="apqa-rule-compact-comment">{{ record.comment }}</span>
  </div>
  <div class="apqa-rule-compact-definition">
    <cmdlet-chain :chain="record.left" />
    <comparison :op="record.op" />
    <cmdlet-chain :chain="record.right" />
  </div>
</li>
`,
};

export default RuleCompact;
