import Rule from './rule';
import RuleCompact from './rule_compact';

// Inner wrapper of a rule record. It holds the rendered rule (compact or full,
// chosen by `expanded`) plus a row of action buttons. The actions are currently
// placeholders — they emit `edit`/`run` for the page to wire up.
const RuleBody = {
  props: ['record', 'expanded'],

  emits: ['toggle', 'edit', 'run'],

  components: {
    'rule': Rule,
    'rule-compact': RuleCompact,
  },

  template: `
<div class="apqa-rule-body">
  <rule-compact v-if="!expanded" :record="record" @toggle="$emit('toggle')" />
  <rule v-else :record="record" @toggle="$emit('toggle')" />

  <div v-if="expanded" class="apqa-rule-body-actions">
    <button type="button" class="apqa-rule-body-action apqa-rule-body-action-edit" @click="$emit('edit', record)">Edit</button>
    <button type="button" class="apqa-rule-body-action apqa-rule-body-action-run" @click="$emit('run', record)">Run</button>
  </div>
</div>
`,
};

export default RuleBody;