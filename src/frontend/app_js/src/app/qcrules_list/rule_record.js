import { computed, ref } from 'vue';

import RuleBody from './rule_body';
import { markClassesForRecord } from './grouping';
import { runTickFor } from './run_result';

// Outer "record" wrapper for a QC rule. It owns the expanded/condensed state and
// toggles it when the inner rule's header is clicked. It forwards
// `edit`/`run`/`delete` actions to the page and, when the rule is the one being
// edited (`editingId`), renders the inline edit form and forwards its
// save/cancel. This is the `<li>` unit rendered inside the rules list.
const RuleRecord = {
  props: {
    record: { type: Object, required: true },
    nodeKey: { type: String, default: '' },
    editingId: { type: String, default: '' },
    runResults: { type: Object, default: () => ({}) },
    cmdlets: { type: Array, default: () => [] },
    ops: { type: Array, default: () => [] },
    tagSuggestions: { type: Array, default: () => [] },
    draggingKey: { type: String, default: '' },
    dropTargetKey: { type: String, default: '' },
    dropPosition: { type: String, default: '' },
  },

  emits: ['edit', 'run', 'delete', 'save', 'cancel', 'handle-down'],

  components: {
    'rule-body': RuleBody,
  },

  template: `
<li :class="classes" :data-node-key="nodeKey">
  <span class="apqa-rules-tree-gutter">
    <button
      type="button"
      class="apqa-rules-tree-handle"
      aria-label="Drag to reorder"
      @pointerdown="onHandleDown"
    >
      <i class="ri-drag-move-2-line" aria-hidden="true"></i>
    </button>
    <span class="apqa-rule-run-tick" :class="tick.cls" :title="tick.title">
      <i v-if="tick.icon" :class="tick.icon"></i>
      <span v-else-if="tick.text" class="apqa-run-tick-text">{{ tick.text }}</span>
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
      const result = [
        'apqa-rules-tree-item',
        'apqa-rule-record',
        ...markClassesForRecord(props.record, props.cmdlets, props.ops),
        ...filterClasses,
      ];
      if (props.nodeKey && props.draggingKey === props.nodeKey) {
        result.push('apqa-is-dragging');
      }
      if (props.nodeKey && props.dropTargetKey === props.nodeKey && props.dropPosition) {
        result.push(`apqa-is-drop-${props.dropPosition}`);
      }
      return result;
    });

    const runResult = computed(() => props.runResults[props.record.id] || null);

    const tick = computed(() => {
      const status = runResult.value && runResult.value.status;
      return runTickFor(status) || { cls: 'is-empty', icon: '', text: '', title: '' };
    });

    function onSave(record, changes) {
      emit('save', record, changes);
    }

    function onCancel(record) {
      emit('cancel', record);
    }

    function onHandleDown(event) {
      emit('handle-down', { record: props.record, event });
    }

    return { expanded, editing, classes, tick, onSave, onCancel, onHandleDown };
  },
};

export default RuleRecord;
