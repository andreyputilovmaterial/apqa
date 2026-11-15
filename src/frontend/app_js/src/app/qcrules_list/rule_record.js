import { computed, ref } from 'vue';

import RuleBody from './rule_body';
import { markClassesForRecord } from './grouping';

// Outer "record" wrapper for a QC rule. It owns the expanded/condensed state and
// toggles it when the inner rule's header is clicked. It forwards
// `edit`/`run`/`delete` actions to the page and, when the rule is the one being
// edited (`editingId`), renders the inline edit form and forwards its
// save/cancel. This is the `<li>` unit rendered inside the rules list.
const RuleRecord = {
  props: {
    record: { type: Object, required: true },
    editingId: { type: String, default: '' },
    runResults: { type: Object, default: () => ({}) },
    cmdlets: { type: Array, default: () => [] },
    ops: { type: Array, default: () => [] },
    tagSuggestions: { type: Array, default: () => [] },
  },

  emits: ['edit', 'run', 'delete', 'save', 'cancel'],

  components: {
    'rule-body': RuleBody,
  },

  template: `
<li :class="classes">
  <span class="apqa-rules-tree-gutter">
    <span class="apqa-rule-run-tick" :class="tickClass" :title="tickTitle">
      <i v-if="tickIcon" :class="tickIcon"></i>
    </span>
  </span>
  <div class="apqa-rules-tree-content">
    <rule-body
      :record="record"
      :expanded="expanded"
      :editing="editing"
      :run-results="runResults"
      :cmdlets="cmdlets"
      :ops="ops"
      :tag-suggestions="tagSuggestions"
      @toggle="expanded = !expanded"
      @edit="$emit('edit', record)"
      @run="$emit('run', record)"
      @delete="$emit('delete', record)"
      @save="onSave"
      @cancel="onCancel"
    />
  </div>
</li>
`,

  setup(props, { emit }) {
    const expanded = ref(false);

    const editing = computed(() =>
      Boolean(props.editingId && props.editingId === props.record.id),
    );

    const classes = computed(() => {
      const filterMeta = props.record._filterMeta;
      const filterClasses =
        filterMeta && Array.isArray(filterMeta.cssClasses)
          ? filterMeta.cssClasses
          : [];
      return [
        'apqa-rules-tree-item',
        'apqa-rule-record',
        ...markClassesForRecord(props.record, props.cmdlets, props.ops),
        ...filterClasses,
      ];
    });

    const runResult = computed(() => props.runResults[props.record.id] || null);

    const tickIcon = computed(() => {
      const status = runResult.value && runResult.value.status;
      if (status === 'passed') return 'ri-check-double-line';
      if (status === 'failed' || status === 'error') return 'ri-close-fill';
      return '';
    });

    const tickClass = computed(() => {
      const status = runResult.value && runResult.value.status;
      if (status === 'passed') return 'is-passed';
      if (status === 'failed' || status === 'error') return 'is-failed';
      return 'is-empty';
    });

    const tickTitle = computed(() => {
      const status = runResult.value && runResult.value.status;
      if (status === 'passed') return 'Passed';
      if (status === 'failed') return 'Failed';
      if (status === 'error') return 'Run failed';
      return '';
    });

    function onSave(record, changes) {
      emit('save', record, changes);
    }

    function onCancel(record) {
      emit('cancel', record);
    }

    return { expanded, editing, classes, tickIcon, tickClass, tickTitle, onSave, onCancel };
  },
};

export default RuleRecord;
