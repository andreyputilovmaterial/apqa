import { computed, onUnmounted, reactive, ref, watch } from 'vue';

import AliasRecord from './alias_record';
import GroupEditForm from './group_edit_form';
import MarksBadges from './marks_badges';
import RuleRecord from './rule_record';
import { buildGroupNodes } from './grouping';
import { moveDescriptor } from './reorder';
import { runTickFor, groupRunSummary } from './run_result';

// Foldable tree of QC rules: renders folders (groups) and rules as a single
// depth-first list, indenting by depth and hiding every descendant of a
// collapsed folder. Rules are always-shown cards (no expand/collapse); folders
// keep a [+]/[-] toggle. Both kinds emit their edit/run/delete actions up to
// the page (rules via `edit`/`run`/`delete`, folders via the `-group` events).
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
    editingGroupId: { type: String, default: '' },
    runResults: { type: Object, default: () => ({}) },
    emptyRunGroups: { type: Object, default: () => ({}) },
    cmdlets: { type: Array, default: () => [] },
    ops: { type: Array, default: () => [] },
    tagSuggestions: { type: Array, default: () => [] },
  },

  emits: ['edit', 'run', 'duplicate', 'delete', 'save', 'cancel', 'reorder', 'edit-group', 'run-group', 'add-rule', 'add-subfolder', 'delete-group', 'save-group', 'cancel-group'],

  components: {
    'alias-record': AliasRecord,
    'group-edit-form': GroupEditForm,
    'marks-badges': MarksBadges,
    'rule-record': RuleRecord,
  },

  template: `
<div ref="rootEl" class="apqa-rules-tree" @pointerdown.capture="onHeaderPointerDown" @click.capture="onClickCapture">
  <ul class="apqa-rules-tree-list">
    <template v-for="node in pagedNodes" :key="node.key">
      <li v-if="node.kind === 'group'" class="apqa-rules-tree-item apqa-rules-tree-group" :class="itemClasses(node)" :data-node-key="node.key" :style="{ '--rules-tree-depth': node.depth }">
        <span class="apqa-rules-tree-gutter">
          <span v-if="node.tick" class="apqa-rule-run-tick" :class="node.tick.cls" :title="node.tick.title">
            <i v-if="node.tick.icon" :class="node.tick.icon"></i>
            <span v-else-if="node.tick.text" class="apqa-run-tick-text">{{ node.tick.text }}</span>
          </span>
        </span>
        <div class="apqa-rules-tree-content">
          <group-edit-form
            v-if="isEditingGroup(node)"
            :group="node"
            :collapsed="Boolean(collapsed[node.id])"
            :tag-suggestions="tagSuggestions"
            @save="onSaveGroup(node, $event)"
            @cancel="onCancelGroup(node)"
          />
          <div v-else class="apqa-qcrules-entry apqa-qcrules-entry-folder apqa-rules-tree-group-card">
            <div
              class="apqa-rules-tree-group-header"
              role="button"
              tabindex="0"
              :aria-expanded="String(!collapsed[node.id])"
              @click="toggle(node)"
              @keydown.enter.prevent="toggle(node)"
            >
              <span class="apqa-rules-tree-group-header-row">
                <span class="apqa-rules-tree-group-toggle" aria-hidden="true">{{ collapsed[node.id] ? '[+]' : '[-]' }}</span>
                <span class="apqa-rules-tree-group-name">{{ node.name }}</span>
              </span>
              <span v-if="node.comment" class="apqa-rules-tree-group-comment">{{ node.comment }}</span>
            </div>

            <div class="apqa-record-actions">
              <button type="button" class="apqa-record-action apqa-record-action-edit" title="Edit" aria-label="Edit folder" @click="$emit('edit-group', node)">
                <i class="ri-edit-box-line" aria-hidden="true"></i>
              </button>
              <button type="button" class="apqa-record-action apqa-record-action-run" title="Run" aria-label="Run folder" @click="$emit('run-group', node)">
                <i class="ri-play-large-line" aria-hidden="true"></i>
              </button>
              <button type="button" class="apqa-record-action apqa-record-action-add" title="Add QC rule" aria-label="Add QC rule to folder" @click="$emit('add-rule', node)">
                <i class="ri-add-large-fill" aria-hidden="true"></i>
              </button>
              <button type="button" class="apqa-record-action apqa-record-action-add-subfolder" title="Add subfolder" aria-label="Add subfolder to folder" @click="$emit('add-subfolder', node)">
                <i class="ri-folder-add-line" aria-hidden="true"></i>
              </button>
              <button type="button" class="apqa-record-action apqa-record-action-delete" title="Delete" aria-label="Delete folder" @click="$emit('delete-group', node)">
                <i class="ri-delete-bin-6-line" aria-hidden="true"></i>
              </button>
            </div>

            <div v-if="hasRunSummary(node)" class="apqa-rules-tree-group-run-result">
              <div class="apqa-rules-tree-group-run-result-status" :class="runSummaryClass(node)">{{ runSummaryText(node) }}</div>
            </div>

            <div v-if="(node.tags && node.tags.length) || node.marks.length" class="apqa-record-meta">
              <span v-if="node.tags && node.tags.length" class="apqa-record-tags">{{ node.tags.join(', ') }}</span>
              <span v-if="node.marks.length" class="apqa-rules-tree-group-marks">
                <span class="apqa-rules-tree-group-marks-label">includes rules marked</span>
                <marks-badges :marks="node.marks" />
              </span>
            </div>
          </div>
          <ul v-if="!collapsed[node.id] && node.aliases.length" class="apqa-rules-tree-aliases">
            <alias-record v-for="alias in node.aliases" :key="alias.name" :alias="alias" :cmdlets="cmdlets" />
          </ul>
          <p v-if="!collapsed[node.id] && !node.hasChildren" class="apqa-rules-tree-group-empty">Nothing to show</p>
        </div>
      </li>
      <rule-record
        v-else
        :record="node.record"
        :node-key="node.key"
        :style="{ '--rules-tree-depth': node.depth }"
        :editing-id="editingId"
        :run-results="runResults"
        :cmdlets="cmdlets"
        :ops="ops"
        :tag-suggestions="tagSuggestions"
        :dragging-key="drag.draggingKey"
        :drop-target-key="drag.targetKey"
        :drop-position="drag.position"
        @edit="$emit('edit', $event)"
        @run="$emit('run', $event)"
        @duplicate="$emit('duplicate', $event)"
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
    // Group ids the tree has already seen, so a reload can tell a "new folder"
    // (fold it) apart from an "existing folder" (leave its state alone).
    const knownGroupIds = new Set();
    const page = ref(0);
    const rootEl = ref(null);

    // Drag state. `draggingKey` is the `key` of the node being dragged; while it
    // is set, `targetKey`/`position` describe the current drop target
    // (`position` is 'before' | 'after' | 'inside').
    const drag = reactive({ draggingKey: '', targetKey: '', position: '', suppressClick: false });

    // Pending pointer gesture. A mouse pointer starts a drag as soon as it moves
    // past a small threshold; a touch pointer only starts after a press-and-hold,
    // so a quick swipe keeps scrolling the page and a tap still toggles.
    const pointer = {
      active: false,
      dragging: false,
      nodeKey: '',
      startX: 0,
      startY: 0,
      holdTimer: null,
    };

    // A drag may start only from a rule/folder header — not from the inline edit
    // form, the action buttons, the definition chips, or the mark badges.
    const DRAG_SURFACE_SELECTOR =
      '.apqa-rules-tree-group-header, .apqa-rule-card-head';
    const MOUSE_DRAG_THRESHOLD = 8;
    const TOUCH_HOLD_MS = 400;
    const TOUCH_SLOP = 10;

    // Every folder starts folded. On a group reload we only fold folders that
    // are new to the tree (and prune removed ones) — existing folders keep their
    // open/closed state, so a reorder (which reloads the groups) does not
    // collapse the folder the user just rearranged. Skipped while a rule is
    // being edited, so a group mutation elsewhere cannot collapse the folder and
    // destroy the inline form.
    watch(
      () => props.groups,
      (groups) => {
        if (props.editingId || props.editingGroupId) return;
        const current = new Set(groups.map((group) => group.id));
        for (const id of current) {
          if (!knownGroupIds.has(id)) collapsed[id] = true;
        }
        for (const key of Object.keys(collapsed)) {
          if (!current.has(key)) delete collapsed[key];
        }
        knownGroupIds.clear();
        for (const id of current) knownGroupIds.add(id);
      },
      { immediate: true },
    );

    const nodes = computed(() => buildGroupNodes(props.groups, props.records, props.cmdlets, props.ops, props.runResults));
    const nodeByKey = computed(() => {
      const map = new Map();
      for (const node of nodes.value) map.set(node.key, node);
      return map;
    });
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
      return visibleNodes.value.slice(start, start + perPage.value).map((node) => {
        if (node.kind !== 'group') return node;
        return { ...node, tick: runTickFor(node.runStatus) };
      });
    });

    function editingNode() {
      if (!props.editingId) return null;
      return (
        nodes.value.find(
          (node) => node.kind === 'rule' && node.record.id === props.editingId,
        ) || null
      );
    }

    function editingGroupNode() {
      if (!props.editingGroupId) return null;
      return (
        nodes.value.find(
          (node) => node.kind === 'group' && node.id === props.editingGroupId,
        ) || null
      );
    }

    // Folder "last run" summary, mirroring a rule's cached run-result banner. It
    // is shown once at least one rule inside has a result (passed/failed/errored/
    // running), or when an empty folder was run (a "no tests ran" note). A folder
    // whose rules were never run stays blank, and an untouched empty folder shows
    // nothing.
    function hasRunSummary(node) {
      if (isEmptyRun(node)) return true;
      const agg = node.runAggregate;
      return Boolean(
        agg && agg.total > 0 && agg.passed + agg.failed + agg.errored + agg.running > 0,
      );
    }

    // A folder whose "Run" was clicked while it contained no rules (recursively)
    // — the page remembers the click so we can show a "no tests ran" note in the
    // same spot a real run summary appears, instead of a browser alert.
    function isEmptyRun(node) {
      return Boolean(
        node.kind === 'group' &&
        node.runAggregate &&
        node.runAggregate.total === 0 &&
        props.emptyRunGroups[node.id],
      );
    }

    function runSummaryText(node) {
      if (isEmptyRun(node)) return 'no tests ran';
      return groupRunSummary(node.runAggregate);
    }

    function runSummaryClass(node) {
      if (isEmptyRun(node)) return 'apqa-rule-run-result-running';
      switch (node.runStatus) {
        case 'passed':
          return 'apqa-rule-run-result-passed';
        case 'failed':
          return 'apqa-rule-run-result-failed';
        default:
          return 'apqa-rule-run-result-running';
      }
    }

    function warnEditing() {
      window.alert('Finish or cancel editing before changing this view.');
    }

    function toggle(node) {
      // Refuse to collapse a folder while a rule or folder inside it is being
      // edited, so the inline form (and its unsaved changes) is not destroyed.
      if (node.kind === 'group') {
        const target = editingNode();
        const groupTarget = editingGroupNode();
        const hidesRule = target && target.parents.includes(node.id);
        const hidesGroup =
          groupTarget &&
          (groupTarget.id === node.id || groupTarget.parents.includes(node.id));
        if (!collapsed[node.id] && (hidesRule || hidesGroup)) {
          warnEditing();
          return;
        }
      }
      if (collapsed[node.id]) delete collapsed[node.id];
      else collapsed[node.id] = true;
    }

    function goToPage(index) {
      if ((props.editingId || props.editingGroupId) && index !== page.value) {
        warnEditing();
        return;
      }
      page.value = index;
    }

    function isEditingGroup(node) {
      return Boolean(props.editingGroupId && props.editingGroupId === node.id);
    }

    function onSave(record, changes) {
      emit('save', record, changes);
    }

    function onCancel(record) {
      emit('cancel', record);
    }

    function onSaveGroup(node, changes) {
      emit('save-group', node, changes);
    }

    function onCancelGroup(node) {
      emit('cancel-group', node);
    }

    function itemClasses(node) {
      const classes = [...(node.markClasses || [])];
      if (drag.draggingKey === node.key) classes.push('apqa-is-dragging');
      if (drag.targetKey === node.key && drag.position) {
        classes.push(`apqa-is-drop-${drag.position}`);
      }
      return classes;
    }

    // ---- drag & drop ---------------------------------------------------------

    function isPrimaryPointer(event) {
      if (event.pointerType === 'mouse' && event.button !== 0) return false;
      return true;
    }

    // Delegated from the tree root: a press on a rule/folder header starts a
    // candidate drag. A mouse pointer starts dragging as soon as it moves past
    // `MOUSE_DRAG_THRESHOLD`; a touch pointer requires a press-and-hold so the
    // header stays scrollable and a tap still toggles.
    function onHeaderPointerDown(event) {
      // A fresh gesture clears any stale click suppression left by a previous
      // drag that produced no click (e.g. a touch drag).
      drag.suppressClick = false;

      const target = event.target;
      const surface =
        target && target.closest ? target.closest(DRAG_SURFACE_SELECTOR) : null;
      if (!surface) return;
      // The inline edit forms reuse the same header classes for a stable look,
      // but their headers are labels, not reorder drag surfaces.
      if (surface.closest('.apqa-rule-edit-form, .apqa-group-edit-form')) return;
      const item = target.closest('[data-node-key]');
      if (!item) return;
      const key = item.getAttribute('data-node-key');
      if (!nodeByKey.value.has(key) || !isPrimaryPointer(event)) return;

      pointer.active = true;
      pointer.dragging = false;
      pointer.nodeKey = key;
      pointer.startX = event.clientX ?? 0;
      pointer.startY = event.clientY ?? 0;

      if (event.pointerType === 'touch') {
        pointer.holdTimer = window.setTimeout(() => startDrag(key), TOUCH_HOLD_MS);
        if (rootEl.value) {
          rootEl.value.addEventListener('touchmove', onTouchMove, { passive: false });
          rootEl.value.addEventListener('touchend', onTouchEnd);
          rootEl.value.addEventListener('touchcancel', onTouchEnd);
        }
      } else {
        window.addEventListener('pointermove', onPointerMove, { passive: false });
        window.addEventListener('pointerup', onPointerUp);
        window.addEventListener('pointercancel', onPointerUp);
      }
    }

    function startDrag(key) {
      if (!pointer.active) return;
      pointer.dragging = true;
      pointer.holdTimer = null;
      drag.draggingKey = key;
      drag.targetKey = '';
      drag.position = '';
      drag.suppressClick = true;
    }

    function onPointerMove(event) {
      if (!pointer.active) return;
      if (!pointer.dragging) {
        const dx = (event.clientX ?? pointer.startX) - pointer.startX;
        const dy = (event.clientY ?? pointer.startY) - pointer.startY;
        if (dx * dx + dy * dy < MOUSE_DRAG_THRESHOLD * MOUSE_DRAG_THRESHOLD) return;
        startDrag(pointer.nodeKey);
      }
      event.preventDefault();
      updateDropTarget(event.clientY ?? pointer.startY);
    }

    function onTouchMove(event) {
      if (!pointer.active) return;
      const touch = event.touches && event.touches[0];
      if (!touch) return;
      if (!pointer.dragging) {
        const dx = touch.clientX - pointer.startX;
        const dy = touch.clientY - pointer.startY;
        if (dx * dx + dy * dy <= TOUCH_SLOP * TOUCH_SLOP) return;
        // Moved too far before the hold fired: it is a scroll/tap, abandon it.
        cleanupDrag();
        return;
      }
      // The hold fired — take over the gesture so the page stops scrolling.
      event.preventDefault();
      updateDropTarget(touch.clientY);
    }

    function updateDropTarget(clientY) {
      const drop = computeDropTarget(clientY);
      if (drop.targetKey !== drag.targetKey || drop.position !== drag.position) {
        drag.targetKey = drop.targetKey;
        drag.position = drop.position;
      }
    }

    function onPointerUp() {
      finishDrag();
    }

    function onTouchEnd() {
      finishDrag();
    }

    function finishDrag() {
      const descriptor = currentDescriptor();
      cleanupDrag();
      if (descriptor) emit('reorder', descriptor);
    }

    function onClickCapture(event) {
      if (!drag.suppressClick) return;
      event.stopPropagation();
      drag.suppressClick = false;
    }

    function currentDescriptor() {
      const dragged = nodeByKey.value.get(drag.draggingKey);
      const target = nodeByKey.value.get(drag.targetKey);
      if (!dragged || !target || !drag.position) return null;
      return moveDescriptor(dragged, target, drag.position, nodes.value);
    }

    function resolvePosition(key, y, rect) {
      const node = nodeByKey.value.get(key);
      if (!node) return '';
      const height = rect.height || 1;
      if (y < rect.top + height * 0.25) return 'before';
      if (y > rect.top + height * 0.75) return 'after';
      if (node.kind === 'group') return 'inside';
      return y < rect.top + height / 2 ? 'before' : 'after';
    }

    function computeDropTarget(y) {
      const root = rootEl.value;
      if (!root) return { targetKey: '', position: '' };
      const items = Array.from(root.querySelectorAll('.apqa-rules-tree-item'));
      const GAP = 4;
      let first = null;
      let last = null;
      for (const el of items) {
        const key = el.getAttribute('data-node-key');
        if (!key || key === drag.draggingKey) continue;
        const rect = el.getBoundingClientRect();
        if (!first || rect.top < first.rect.top) first = { key, rect };
        if (!last || rect.bottom > last.rect.bottom) last = { key, rect };
        if (y >= rect.top - GAP && y <= rect.bottom + GAP) {
          return { targetKey: key, position: resolvePosition(key, y, rect) };
        }
      }
      if (first && y < first.rect.top) return { targetKey: first.key, position: 'before' };
      if (last && y > last.rect.bottom) return { targetKey: last.key, position: 'after' };
      return { targetKey: '', position: '' };
    }

    function cleanupDrag() {
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
      window.removeEventListener('pointercancel', onPointerUp);
      if (rootEl.value) {
        rootEl.value.removeEventListener('touchmove', onTouchMove);
        rootEl.value.removeEventListener('touchend', onTouchEnd);
        rootEl.value.removeEventListener('touchcancel', onTouchEnd);
      }
      if (pointer.holdTimer) {
        window.clearTimeout(pointer.holdTimer);
        pointer.holdTimer = null;
      }
      pointer.active = false;
      pointer.dragging = false;
      pointer.nodeKey = '';
      pointer.startX = 0;
      pointer.startY = 0;
      drag.draggingKey = '';
      drag.targetKey = '';
      drag.position = '';
    }

    onUnmounted(cleanupDrag);

    return {
      rootEl,
      collapsed,
      page,
      numPages,
      pagedNodes,
      drag,
      itemClasses,
      toggle,
      goToPage,
      isEditingGroup,
      onSave,
      onCancel,
      onSaveGroup,
      onCancelGroup,
      hasRunSummary,
      runSummaryText,
      runSummaryClass,
      onHeaderPointerDown,
      onClickCapture,
    };
  },
};

export default RulesTree;

