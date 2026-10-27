import { computed, reactive, ref, watch } from 'vue';

import AliasRecord from './alias_record';
import MarksBadges from './marks_badges';
import RuleRecord from './rule_record';
import { buildGroupNodes } from './grouping';

// Foldable tree of QC rules: renders folders (groups) and rules as a single
// depth-first list, indenting by depth and hiding every descendant of a
// collapsed folder. Rules reuse the existing `rule-record` component, so each
// rule still expands/collapses and emits its edit/run actions up to the page.
//
// Pagination applies to the *visible* node list (folder headings and rule
// leaves alike), so both "many rules in a folder" and "many folders at a
// level" page the same way a flat list would.
const RulesTree = {
  props: {
    records: { type: Array, default: () => [] },
    groups: { type: Array, default: () => [] },
    recordsPerPage: { type: Number, default: 25 },
  },

  emits: ['edit', 'run', 'delete'],

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
        @edit="$emit('edit', $event)"
        @run="$emit('run', $event)"
        @delete="$emit('delete', $event)"
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
      @click="page = n - 1"
    >
      {{ n }}
    </button>
  </div>
</div>
`,

  setup(props) {
    const collapsed = reactive({});
    const page = ref(0);

    // Every folder starts folded. Re-fold whenever the group set is (re)loaded,
    // e.g. after creating/renaming/deleting a group via the page.
    watch(
      () => props.groups,
      () => {
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

    function toggle(node) {
      if (collapsed[node.id]) delete collapsed[node.id];
      else collapsed[node.id] = true;
    }

    return { collapsed, page, numPages, pagedNodes, toggle };
  },
};

export default RulesTree;
