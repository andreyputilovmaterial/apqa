import Rule from './rule';
import RuleCompact from './rule_compact';

// Inner wrapper of a rule record. It holds the rendered rule (compact or full,
// chosen by `expanded`) plus a row of action buttons (Edit/Run/Delete). Edit/Run
// are still placeholders; Delete is wired through the page to the CRUD endpoint.
const RuleBody = {
  props: ['record', 'expanded'],

  emits: ['toggle', 'edit', 'run', 'delete'],

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
    <button type="button" class="apqa-rule-body-action apqa-rule-body-action-delete" @click="$emit('delete', record)">Delete</button>
  </div>
</div>
`,
};

export default RuleBody;