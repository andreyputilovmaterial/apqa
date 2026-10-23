import { ref } from 'vue';

import RuleBody from './rule_body';

// Outer "record" wrapper for a QC rule. It owns the expanded/condensed state and
// toggles it when the inner rule's header is clicked. It forwards `edit`/`run`
// actions to the page. This is the `<li>` unit rendered inside the rules list.
const RuleRecord = {
  props: ['record'],

  emits: ['edit', 'run'],

  components: {
    'rule-body': RuleBody,
  },

  template: `
<li class="apqa-rule-record" :class="record._filterMeta.cssClasses">
  <rule-body
    :record="record"
    :expanded="expanded"
    @toggle="expanded = !expanded"
    @edit="$emit('edit', record)"
    @run="$emit('run', record)"
  />
</li>
`,

  setup() {
    const expanded = ref(false);
    return { expanded };
  },
};

export default RuleRecord;