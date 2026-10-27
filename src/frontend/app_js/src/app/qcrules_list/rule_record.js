import { computed, ref } from 'vue';

import RuleBody from './rule_body';
import { markClassesForRecord } from './grouping';

// Outer "record" wrapper for a QC rule. It owns the expanded/condensed state and
// toggles it when the inner rule's header is clicked. It forwards
// `edit`/`run`/`delete` actions to the page. This is the `<li>` unit rendered
// inside the rules list. Its classes are the shared tree-entry base plus the
// rule kind marker, the rule's mark classes, and any classes the records filter
// attached (e.g. `.apqa-u-hidden`).
const RuleRecord = {
  props: ['record'],

  emits: ['edit', 'run', 'delete'],

  components: {
    'rule-body': RuleBody,
  },

  template: `
<li :class="classes">
  <rule-body
    :record="record"
    :expanded="expanded"
    @toggle="expanded = !expanded"
    @edit="$emit('edit', record)"
    @run="$emit('run', record)"
    @delete="$emit('delete', record)"
  />
</li>
`,

  setup(props) {
    const expanded = ref(false);

    const classes = computed(() => {
      const filterMeta = props.record._filterMeta;
      const filterClasses =
        filterMeta && Array.isArray(filterMeta.cssClasses)
          ? filterMeta.cssClasses
          : [];
      return [
        'apqa-rules-tree-item',
        'apqa-rule-record',
        ...markClassesForRecord(props.record),
        ...filterClasses,
      ];
    });

    return { expanded, classes };
  },
};

export default RuleRecord;