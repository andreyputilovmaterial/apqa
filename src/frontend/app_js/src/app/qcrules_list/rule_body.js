import Rule from './rule';
import RuleCompact from './rule_compact';
import RuleEditForm from './rule_edit_form';

// Inner wrapper of a rule record. When not editing it holds the rendered rule
// (compact or full, chosen by `expanded`) plus a row of action buttons
// (Edit/Run/Delete). When `editing` is true the rule display is replaced by the
// inline edit form, whose save/cancel are forwarded up with the record.
const RuleBody = {
  props: {
    record: { type: Object, required: true },
    expanded: { type: Boolean, default: false },
    editing: { type: Boolean, default: false },
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
    <rule-compact v-if="!expanded" :record="record" @toggle="$emit('toggle')" />
    <rule v-else :record="record" @toggle="$emit('toggle')" />

    <div v-if="expanded" class="apqa-rule-body-actions">
      <button type="button" class="apqa-rule-body-action apqa-rule-body-action-edit" @click="$emit('edit', record)">Edit</button>
      <button type="button" class="apqa-rule-body-action apqa-rule-body-action-run" @click="$emit('run', record)">Run</button>
      <button type="button" class="apqa-rule-body-action apqa-rule-body-action-delete" @click="$emit('delete', record)">Delete</button>
    </div>
  </template>
</div>
`,
};

export default RuleBody;
