import { computed, reactive, ref, watch } from 'vue';

import AliasRecord from './alias_record';
import MarksBadges from './marks_badges';
import RuleRecord from './rule_record';
import { buildGroupNodes } from './grouping';

// Foldable tree of QC rules: renders folders (groups) and rules as a single
// depth-first list, indenting by depth and hiding every descendant of a
// collapsed folder. Rules reuse the existing `rule-record` component, so each
// rule still expands/collapses and emits its edit/run/delete/save/cancel
// actions up to the page.
//
// While a rule is being edited (`editingId` is set), the tree refuses to
// collapse the folder that contains it (or change pagination), so the inline
// edit form is not destroyed and unsaved changes are not silently dropped.
const RulesTree = {
  props: {
    records: { type: Array, default: () => [] },
    groups: { type: Array, default: () => [] },
    recordsPerPage: { type: Number, default: 25 },
    editingId: { type: String, default: '' },
    cmdlets: { type: Array, default: () => [] },
    ops: { type: Array, default: () => [] },
    tagSuggestions: { type: Array, default: () => [] },
  },

  emits: ['edit', 'run', 'delete', 'save', 'cancel'],

  components: {
    'alias-record': AliasRecord,
    'marks-badges': MarksBadges,
    'rule-record': RuleRecord,
  },

  template: `
<div class="apqa-rules-tree">
  <ul class="apqa-rules-tree-list">
    <template v-for="node in pagedNodes" :key="node.key">
      <li v-if="node.kind === 'group'" class="apqa-rules-tree-item apqa-rules-tree-group" :class="node.markClasses" :style="{ '--rules-tree-depth': node.depth }">
        <button
          type="button"
          class="apqa-qcrules-entry apqa-qcrules-entry-folder apqa-rules-tree-group-header"
          :aria-expanded="String(!collapsed[node.id])"
          @click="toggle(node)"
        >
          <span class="apqa-rules-tree-group-header-row">
            <span class="apqa-rules-tree-group-toggle" aria-hidden="true">{{ collapsed[node.id] ? '[+]' : '[-]' }}</span>
            <span class="apqa-rules-tree-group-name">{{ node.name }}</span>
          </span>
          <span v-if="node.marks.length" class="apqa-rules-tree-group-marks">
            <span class="apqa-rules-tree-group-marks-label">includes rules marked</span>
            <marks-badges :marks="node.marks" />
          </span>
        </button>
        <ul v-if="!collapsed[node.id] && node.aliases.length" class="apqa-rules-tree-aliases">
          <alias-record v-for="alias in node.aliases" :key="alias.name" :alias="alias" />
        </ul>
      </li>
      <rule-record
        v-else
        :record="node.record"
        :style="{ '--rules-tree-depth': node.depth }"
        :editing-id="editingId"
        :cmdlets="cmdlets"
        :ops="ops"
        :tag-suggestions="tagSuggestions"
        @edit="$emit('edit', $event)"
        @run="$emit('run', $event)"
        @delete="$emit('delete', $event)"
        @save="onSave"
        @cancel="onCancel"
      />
    </template>
  </ul>

  <div v-if="numPages > 1" class="apqa-rules-tree-pagination">
    <button
      v-for="n in numPages"
      :key="n"
      type="button"
      class="apqa-rules-tree-page"
      :class="{ 'is-active': n - 1 === page }"
      @click="goToPage(n - 1)"
    >
      {{ n }}
    </button>
  </div>
</div>
`,

  setup(props, { emit }) {
    const collapsed = reactive({});
    const page = ref(0);

    // Every folder starts folded. Re-fold whenever the group set is (re)loaded,
    // e.g. after creating/renaming/deleting a group via the page — but skip the
    // reset while a rule is being edited, so a group mutation elsewhere cannot
    // collapse the folder and destroy the inline form.
    watch(
      () => props.groups,
      () => {
        if (props.editingId) return;
        for (const key of Object.keys(collapsed)) delete collapsed[key];
        for (const group of props.groups) collapsed[group.id] = true;
      },
      { immediate: true },
    );

    const nodes = computed(() => buildGroupNodes(props.groups, props.records));
    const visibleNodes = computed(() =>
      nodes.value.filter((node) => !node.parents.some((parent) => collapsed[parent])),
    );

    const perPage = computed(() =>
      props.recordsPerPage > 0 ? props.recordsPerPage : Math.max(1, visibleNodes.value.length),
    );
    const numPages = computed(() =>
      Math.max(1, Math.ceil(visibleNodes.value.length / perPage.value)),
    );

    // Keep `page` in range when collapsing folders (or reloading) shrinks the list.
    watch(numPages, (n) => {
      if (page.value >= n) page.value = 0;
    });

    const pagedNodes = computed(() => {
      const start = page.value * perPage.value;
      return visibleNodes.value.slice(start, start + perPage.value);
    });

    function editingNode() {
      if (!props.editingId) return null;
      return (
        nodes.value.find(
          (node) => node.kind === 'rule' && node.record.id === props.editingId,
        ) || null
      );
    }

    function warnEditing() {
      window.alert('Finish or cancel editing the rule before changing this view.');
    }

    function toggle(node) {
      // Refuse to collapse a folder while a rule inside it is being edited, so
      // the inline form (and its unsaved changes) is not destroyed.
      if (node.kind === 'group') {
        const target = editingNode();
        if (!collapsed[node.id] && target && target.parents.includes(node.id)) {
          warnEditing();
          return;
        }
      }
      if (collapsed[node.id]) delete collapsed[node.id];
      else collapsed[node.id] = true;
    }

    function goToPage(index) {
      if (props.editingId && index !== page.value) {
        warnEditing();
        return;
      }
      page.value = index;
    }

    function onSave(record, changes) {
      emit('save', record, changes);
    }

    function onCancel(record) {
      emit('cancel', record);
    }

    return { collapsed, page, numPages, pagedNodes, toggle, goToPage, onSave, onCancel };
  },
};

export default RulesTree;

