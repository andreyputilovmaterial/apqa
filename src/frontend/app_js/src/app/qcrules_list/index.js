import { computed, ref, reactive, onMounted, defineComponent, h } from 'vue';

import { makeFetchResponseErrorMessage } from '@/common_defs/helper_functions';
import logError from '@/common_components/log_error';
import { createModal } from '@/common_components/modals/modals';
import RuleRecord from './rule_record';
import RulesTree from './rules_tree';
import RuleForm from './rule_form';
import GroupForm from './group_form';
import RuleDeleteConfirm from './rule_delete_confirm';
import { allRulesInOrder, rulesForGroup } from './grouping';
import { groupRunSummary } from './run_result';

import './styles.css';

function toRecord(rule) {
  const meta = rule.meta || {};
  return {
    id: rule.id || '',
    name: rule.name || '',
    group: rule.group || '',
    order: meta.order ?? 0,
    op: rule.op || '',
    op_args: rule.op_args && typeof rule.op_args === 'object' ? { ...rule.op_args } : {},
    comment: meta.comment || '',
    tags: Array.isArray(meta.tags) ? meta.tags.slice() : [],
    created_at: meta.created_at || '',
    modified_at: meta.modified_at || '',
    markers: Array.isArray(meta.markers) ? meta.markers : [],
    left: Array.isArray(rule.left) ? rule.left : [],
    right: Array.isArray(rule.right) ? rule.right : [],
    meta: { ...meta },
  };
}

function toAlias(alias) {
  return {
    name: alias.name || '',
    chain: Array.isArray(alias.chain) ? alias.chain : [],
  };
}

function toGroupRecord(group) {
  const meta = group.meta || {};
  return {
    id: group.id || '',
    name: group.name || '',
    parent: group.parent || '',
    order: meta.order ?? 0,
    comment: meta.comment || '',
    tags: Array.isArray(meta.tags) ? meta.tags.slice() : [],
    aliases: Array.isArray(group.aliases) ? group.aliases.map(toAlias) : [],
    meta,
  };
}

const QcRulesList = {
  components: {
    'rule-record': RuleRecord,
    'rules-tree': RulesTree,
  },

  template: `
<div class="apqa-qcrules-page">
  <div v-if="loading" class="apqa-qcrules-page-state">Loading QC rules...</div>
  <div v-else-if="loadError" class="apqa-qcrules-page-state apqa-qcrules-page-state-error">{{ loadError }}</div>
  <template v-else>
    <div class="apqa-qcrules-page-intro">
      <p>Define QC tests once and reuse them across projects.</p>
      <p>Run tests manually or automatically.</p>
      <p>Compare data and metadata across different sources and deliverables. Detect unexpected changes, inconsistencies, missing information, and violations of predefined rules.</p>
    </div>

    <section class="apqa-qcrules-page-section">
      <h2 class="apqa-qcrules-page-section-title">QC rules</h2>

      <div class="apqa-qcrules-page-actions">
        <button type="button" class="apqa-record-action apqa-record-action-create-rule" title="Create new QC rule" aria-label="Create new QC rule" @click="createRule">
          <i class="ri-add-large-fill" aria-hidden="true"></i>
        </button>
        <button type="button" class="apqa-record-action apqa-record-action-create-folder" title="Create folder" aria-label="Create folder" @click="createFolder">
          <i class="ri-folder-add-line" aria-hidden="true"></i>
        </button>
        <button type="button" class="apqa-record-action apqa-record-action-run-all" title="Run all tests" aria-label="Run all tests" @click="onRunAll">
          <i class="ri-play-large-line" aria-hidden="true"></i>
        </button>
      </div>

      <div v-if="hasAllRunSummary" class="apqa-qcrules-page-all-run-result">
        <div class="apqa-qcrules-page-all-run-result-status" :class="allRunSummaryClass">{{ allRunSummaryText }}</div>
      </div>

      <rules-tree :records="records" :groups="groups" :records-per-page="25" :cmdlets="cmdlets" :ops="ops" :tag-suggestions="tagSuggestions" :editing-id="editingId" :editing-group-id="editingGroupId" :run-results="runResults" :empty-run-groups="emptyRunGroups" @edit="onEditRule" @run="onRunRule" @duplicate="onDuplicateRule" @delete="onDeleteRule" @edit-group="onEditGroup" @run-group="onRunGroup" @add-rule="onAddRuleToGroup" @add-subfolder="onAddSubfolder" @delete-group="onDeleteGroup" @save="onSaveRule" @cancel="onCancelEdit" @save-group="onSaveGroup" @cancel-group="onCancelGroupEdit" @reorder="onReorder" />
    </section>
  </template>
</div>
`,

  setup() {
    const records = ref([]);
    const groups = ref([]);
    const loading = ref(true);
    const loadError = ref('');
    const cmdletMetadata = ref(null);
    const editingId = ref('');
    const editingGroupId = ref('');

    // Per-rule run results, cached in the UI (keyed by rule id). Kept here, on
    // the page, rather than on the record objects themselves, so the cached
    // result survives list reloads and tree recomputes until the rule is
    // edited/deleted.
    const runResults = reactive({});

    // Folder ids whose "Run" was clicked while the folder contained no QC rules
    // (recursively). Keyed by group id; the tree turns each into a "no tests ran"
    // note in the folder's run-result area instead of a browser alert.
    const emptyRunGroups = reactive({});

    // Whether "Run all" was clicked while there were no rules to run; turns the
    // all-rules summary into a "no tests ran" note (mirrors emptyRunGroups).
    const allRunEmpty = ref(false);

    // Combined run summary over every rule in the list, so the "run all" result
    // area mirrors a folder's last-run summary. Aggregates the same counts as
    // `groupRunAggregate` but over the whole list (ungrouped rules included).
    const allRunAggregate = computed(() => {
      let total = 0;
      let passed = 0;
      let failed = 0;
      let errored = 0;
      let running = 0;
      let blank = 0;
      for (const record of records.value) {
        total += 1;
        const result = runResults[record.id];
        const status = result && result.status ? result.status : 'blank';
        if (status === 'passed') passed += 1;
        else if (status === 'failed') failed += 1;
        else if (status === 'error') errored += 1;
        else if (status === 'running') running += 1;
        else blank += 1;
      }
      return { total, passed, failed, errored, running, blank };
    });

    const allRunStatus = computed(() => {
      const agg = allRunAggregate.value;
      if (agg.total === 0) return 'empty';
      if (agg.failed || agg.errored) return 'failed';
      if (agg.running) return 'running';
      if (agg.passed && !agg.blank) return 'passed';
      if (agg.passed) return 'indeterminate';
      return 'blank';
    });

    const hasAllRunSummary = computed(() => {
      if (allRunEmpty.value && allRunStatus.value === 'empty') return true;
      const agg = allRunAggregate.value;
      return agg.total > 0 && agg.passed + agg.failed + agg.errored + agg.running > 0;
    });

    const allRunSummaryText = computed(() => {
      if (allRunEmpty.value && allRunStatus.value === 'empty') return 'no tests ran';
      return groupRunSummary(allRunAggregate.value);
    });

    const allRunSummaryClass = computed(() => {
      if (allRunEmpty.value && allRunStatus.value === 'empty') return 'apqa-rule-run-result-running';
      switch (allRunStatus.value) {
        case 'passed':
          return 'apqa-rule-run-result-passed';
        case 'failed':
          return 'apqa-rule-run-result-failed';
        default:
          return 'apqa-rule-run-result-running';
      }
    });

    // The create/edit forms need the cmdlet + comparison-op metadata, fetched
    // lazily on first use. These computed refs keep the template readable.
    const cmdlets = computed(() => (cmdletMetadata.value && cmdletMetadata.value.cmdlets) || []);
    const ops = computed(() => (cmdletMetadata.value && cmdletMetadata.value.ops) || []);

    // Distinct tags across loaded rules and folders, used as suggestions in the
    // create/edit forms.
    const tagSuggestions = computed(() => {
      const seen = new Set();
      for (const record of records.value) {
        for (const tag of record.tags) seen.add(tag);
      }
      for (const group of groups.value) {
        for (const tag of group.tags) seen.add(tag);
      }
      return Array.from(seen).sort();
    });

    // Ids already in use, passed to the create form so its generated slug can
    // avoid colliding with an existing rule id.
    const existingRuleIds = computed(() =>
      records.value.map((record) => record.id).filter(Boolean),
    );

    async function requestJson(url) {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(await makeFetchResponseErrorMessage(response));
      }
      return response.json();
    }

    async function load() {
      // `loading` is initialized to true and only ever cleared below, so the
      // spinner shows for the first load. Do not re-set it to true on later
      // reloads (create/delete/save/reorder): toggling it would unmount the
      // rules tree (`v-if="loading"`) and reset every folder's folded state and
      // every rule's expanded state.
      loadError.value = '';
      try {
        const [rulesData, groupsData, metadata] = await Promise.all([
          requestJson('/qc/rules'),
          requestJson('/qc/groups'),
          // Metadata is needed to detect "unfinished" rules (missing required
          // args). It is not critical for listing rules, so a failure here only
          // degrades the unfinished detection to the structural check (empty
          // left/op/right) and is retried when the editor is opened.
          requestJson('/cmdlets/metadata').catch((e) => {
            logError(`Failed to load cmdlet metadata: ${e}`);
            return null;
          }),
        ]);
        records.value = (rulesData.rules || []).map(toRecord);
        groups.value = (groupsData.groups || []).map(toGroupRecord);
        if (metadata) cmdletMetadata.value = metadata;
      } catch (e) {
        loadError.value = `Failed to load QC rules: ${e}`;
        logError(loadError.value);
      } finally {
        loading.value = false;
      }
    }

    async function postJson(url, payload) {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error(await makeFetchResponseErrorMessage(response));
      }
    }

    async function putJson(url, payload) {
      const response = await fetch(url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error(await makeFetchResponseErrorMessage(response));
      }
    }

    async function deleteJson(url) {
      const response = await fetch(url, { method: 'DELETE' });
      if (!response.ok) {
        throw new Error(await makeFetchResponseErrorMessage(response));
      }
    }

    async function ensureCmdletMetadata() {
      if (!cmdletMetadata.value) {
        cmdletMetadata.value = await requestJson('/cmdlets/metadata');
      }
      return cmdletMetadata.value;
    }

    // Open the create-rule modal and resolve with the submitted payload, or null
    // when the user dismisses it. Shared by the top-level "Create new QC rule"
    // button and the per-folder "add" action so both open the same dialog.
    async function openCreateRuleModal() {
      let metadata;
      try {
        metadata = await ensureCmdletMetadata();
      } catch (e) {
        window.alert(`Failed to load cmdlet metadata: ${e}`);
        logError(`Failed to load cmdlet metadata: ${e}`);
        return null;
      }

      const MyForm = defineComponent({
        setup: (_, { attrs }) => () =>
          h(RuleForm, {
            ...attrs,
            cmdlets: metadata.cmdlets || [],
            ops: metadata.ops || [],
            tagSuggestions: tagSuggestions.value,
            existingIds: existingRuleIds.value,
          }),
      });

      try {
        return await createModal(MyForm);
      } catch (e) {
        // Modal dismissed — nothing to create.
        return null;
      }
    }

    async function postNewRule(payload) {
      try {
        await postJson('/qc/rules', payload);
        await load();
      } catch (e) {
        window.alert(`Failed to create QC rule: ${e}`);
        logError(`Failed to create QC rule: ${e}`);
      }
    }

    async function createRule() {
      const payload = await openCreateRuleModal();
      if (!payload) return;

      // Append the new rule at the end of the top-level list: give it an order
      // just past the largest existing order (rules and folders share one order
      // space). Without an explicit order it would sort first, not last.
      let maxOrder = 0;
      for (const record of records.value) {
        if (record.order > maxOrder) maxOrder = record.order;
      }
      for (const group of groups.value) {
        if (group.order > maxOrder) maxOrder = group.order;
      }
      payload.meta = { ...(payload.meta || {}), order: maxOrder + 1 };

      await postNewRule(payload);
    }

    // Same dialog as "Create new QC rule", but the new rule belongs to the
    // clicked folder and is placed last among that folder's direct children
    // (rules in the folder and sub-folders are one interleaved, order-sorted
    // sequence).
    async function onAddRuleToGroup(group) {
      const payload = await openCreateRuleModal();
      if (!payload) return;

      payload.group = group.id;

      let maxOrder = 0;
      for (const record of records.value) {
        if (record.group === group.id && record.order > maxOrder) maxOrder = record.order;
      }
      for (const child of groups.value) {
        if (child.parent === group.id && child.order > maxOrder) maxOrder = child.order;
      }
      payload.meta = { ...(payload.meta || {}), order: maxOrder + 1 };

      await postNewRule(payload);
    }

    // Same dialog as "Create folder", but the new folder is nested under the
    // clicked folder and placed last among its direct children (rules and
    // sub-folders are one interleaved, order-sorted sequence).
    async function onAddSubfolder(group) {
      const payload = await openCreateFolderModal();
      if (!payload) return;

      payload.parent = group.id;

      let maxOrder = 0;
      for (const record of records.value) {
        if (record.group === group.id && record.order > maxOrder) maxOrder = record.order;
      }
      for (const child of groups.value) {
        if (child.parent === group.id && child.order > maxOrder) maxOrder = child.order;
      }
      payload.meta = { ...(payload.meta || {}), order: maxOrder + 1 };

      await postNewFolder(payload);
    }

    async function openCreateFolderModal() {
      const MyForm = defineComponent({
        setup: (_, { attrs }) => () => h(GroupForm, { ...attrs }),
      });

      try {
        return await createModal(MyForm);
      } catch (e) {
        // Modal dismissed — nothing to create.
        return null;
      }
    }

    async function postNewFolder(payload) {
      try {
        await postJson('/qc/groups', payload);
        await load();
      } catch (e) {
        window.alert(`Failed to create folder: ${e}`);
        logError(`Failed to create folder: ${e}`);
      }
    }

    async function createFolder() {
      const payload = await openCreateFolderModal();
      if (!payload) return;

      // Append the new folder at the end of the top-level list: give it an order
      // just past the largest existing order (rules and folders share one order
      // space). Without an explicit order it would sort first, not last.
      let maxOrder = 0;
      for (const record of records.value) {
        if (record.order > maxOrder) maxOrder = record.order;
      }
      for (const group of groups.value) {
        if (group.order > maxOrder) maxOrder = group.order;
      }
      payload.meta = { ...(payload.meta || {}), order: maxOrder + 1 };

      await postNewFolder(payload);
    }

    // Open the inline edit form for a rule. Only one rule can be edited at a
    // time; starting another edit while one is open is blocked so unsaved
    // changes are not silently dropped.
    async function onEditRule(record) {
      if (editingGroupId.value) {
        window.alert('Finish or cancel editing the current folder first.');
        return;
      }
      if (editingId.value && editingId.value !== record.id) {
        window.alert('Finish or cancel editing the current rule first.');
        return;
      }
      try {
        await ensureCmdletMetadata();
      } catch (e) {
        window.alert(`Failed to load cmdlet metadata: ${e}`);
        logError(`Failed to load cmdlet metadata: ${e}`);
        return;
      }
      editingId.value = record.id;
    }

    // Run one QC rule against the backend and cache the result on `runResults`,
    // keyed by rule id. The same runner is used for a single rule and for each
    // rule inside a folder (which runs them one at a time, in tree order).
    async function runRuleRecord(record) {
      runResults[record.id] = { status: 'running' };

      // Run the rule exactly like the backend's "run QC tests" mode does:
      // `tstsuite.py` -> `rule.run()` -> `run_rule(self.to_dict())`. The
      // `/tests/run` endpoint executes the same `run_rule_with_report` path and
      // returns `{result, notes?}` (or `{error}` when a cmdlet raised).
      const payload = {
        name: record.name,
        id: record.id,
        group: record.group,
        meta: { ...(record.meta || {}) },
        left: Array.isArray(record.left) ? record.left : [],
        op: record.op || '',
        op_args: record.op_args && typeof record.op_args === 'object' ? { ...record.op_args } : {},
        right: Array.isArray(record.right) ? record.right : [],
      };

      try {
        const response = await fetch('/tests/run', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        let data = {};
        try {
          data = await response.json();
        } catch (e) {
          data = {};
        }

        if (!response.ok) {
          runResults[record.id] = {
            status: 'error',
            message: (data && data.error) || `HTTP ${response.status}`,
          };
          return;
        }

        runResults[record.id] = {
          status: data && data.result ? 'passed' : 'failed',
          notes: Array.isArray(data && data.notes) ? data.notes : [],
        };
      } catch (e) {
        runResults[record.id] = { status: 'error', message: `${e}` };
      }
    }

    async function onRunRule(record) {
      await runRuleRecord(record);
    }

    // Run every rule in the list one at a time, in the same depth-first order
    // the tree renders them (ungrouped rules and every folder, nested sub-folders
    // included). Each rule updates its own cached result, and the all-rules
    // summary (and each folder tick) re-aggregates as they finish.
    async function onRunAll() {
      const rules = allRulesInOrder(groups.value, records.value);
      if (rules.length === 0) {
        allRunEmpty.value = true;
        return;
      }
      allRunEmpty.value = false;
      for (const record of rules) {
        await runRuleRecord(record);
      }
    }

    // Persist the edits from the inline form. Only the fields the form manages
    // are sent; the existing meta (order, created/modified, unknown keys) is
    // preserved so editing does not reset it.
    async function onSaveRule(record, changes) {
      const meta = { ...(record.meta || {}) };
      if (changes.comment && changes.comment.trim()) meta.comment = changes.comment.trim();
      else delete meta.comment;
      if (Array.isArray(changes.tags) && changes.tags.length) meta.tags = changes.tags.slice();
      else delete meta.tags;
      if (Array.isArray(changes.markers) && changes.markers.length) meta.markers = changes.markers.slice();
      else delete meta.markers;

      const payload = {
        name: changes.name,
        left: Array.isArray(changes.left) ? changes.left : [],
        op: changes.op || '',
        op_args: changes.op_args && typeof changes.op_args === 'object' ? changes.op_args : {},
        right: Array.isArray(changes.right) ? changes.right : [],
        meta,
      };

      try {
        await putJson(`/qc/rules/${encodeURIComponent(record.id)}`, payload);
        editingId.value = '';
        delete runResults[record.id];
        await load();
      } catch (e) {
        window.alert(`Failed to update QC rule: ${e}`);
        logError(`Failed to update QC rule: ${e}`);
      }
    }

    function onCancelEdit() {
      editingId.value = '';
    }

    async function onDuplicateRule(record) {
      try {
        await postJson(`/qc/rules/${encodeURIComponent(record.id)}/duplicate`, {});
        await load();
      } catch (e) {
        window.alert(`Failed to duplicate QC rule: ${e}`);
        logError(`Failed to duplicate QC rule: ${e}`);
      }
    }

    async function onDeleteRule(record) {
      const Confirm = defineComponent({
        setup: (_, { attrs }) => () =>
          h(RuleDeleteConfirm, { ...attrs, record }),
      });

      let confirmed;
      try {
        confirmed = await createModal(Confirm);
      } catch (e) {
        // Modal dismissed — nothing to delete.
        return;
      }

      if (!confirmed) return;

      try {
        await deleteJson(`/qc/rules/${encodeURIComponent(record.id)}`);
        delete runResults[record.id];
        await load();
      } catch (e) {
        window.alert(`Failed to delete QC rule: ${e}`);
        logError(`Failed to delete QC rule: ${e}`);
      }
    }

    // Open the inline edit form for a folder. Only one folder (or rule) can be
    // edited at a time, mirroring the rule edit guard.
    function onEditGroup(group) {
      if (editingId.value) {
        window.alert('Finish or cancel editing the current rule first.');
        return;
      }
      if (editingGroupId.value && editingGroupId.value !== group.id) {
        window.alert('Finish or cancel editing the current folder first.');
        return;
      }
      editingGroupId.value = group.id;
    }

    // Persist the edits from the inline folder form. Only the fields the form
    // manages are sent; the existing meta (order, unknown keys) and aliases are
    // preserved because the backend merges the payload into the stored group.
    async function onSaveGroup(group, changes) {
      const original = groups.value.find((g) => g.id === group.id) || {};
      const meta = { ...(original.meta || {}) };
      if (changes.comment && changes.comment.trim()) meta.comment = changes.comment.trim();
      else delete meta.comment;
      if (Array.isArray(changes.tags) && changes.tags.length) meta.tags = changes.tags.slice();
      else delete meta.tags;

      const payload = {
        name: changes.name,
        parent: original.parent || '',
        meta,
      };

      try {
        await putJson(`/qc/groups/${encodeURIComponent(group.id)}`, payload);
        editingGroupId.value = '';
        await load();
      } catch (e) {
        window.alert(`Failed to update folder: ${e}`);
        logError(`Failed to update folder: ${e}`);
      }
    }

    function onCancelGroupEdit() {
      editingGroupId.value = '';
    }

    async function onRunGroup(group) {
      const rules = rulesForGroup(groups.value, records.value, group.id);
      if (rules.length === 0) {
        emptyRunGroups[group.id] = true;
        return;
      }

      // Run the folder's rules one at a time, in the same depth-first order the
      // tree renders them (nested sub-folders included). Each rule updates its
      // own cached result, and the folder tick re-aggregates from those results,
      // so it stays "Running..." until the last rule finishes.
      for (const record of rules) {
        await runRuleRecord(record);
      }
    }

    async function onDeleteGroup(group) {
      const Confirm = defineComponent({
        setup: (_, { attrs }) => () =>
          h(RuleDeleteConfirm, { ...attrs, record: group, kind: 'folder' }),
      });

      let confirmed;
      try {
        confirmed = await createModal(Confirm);
      } catch (e) {
        // Modal dismissed — nothing to delete.
        return;
      }

      if (!confirmed) return;

      try {
        await deleteJson(`/qc/groups/${encodeURIComponent(group.id)}`);
        await load();
      } catch (e) {
        window.alert(`Failed to delete folder: ${e}`);
        logError(`Failed to delete folder: ${e}`);
      }
    }

    async function onReorder(descriptor) {
      try {
        await postJson('/qc/reorder', descriptor);
        await load();
      } catch (e) {
        window.alert(`Failed to reorder: ${e}`);
        logError(`Failed to reorder: ${e}`);
      }
    }

    onMounted(load);

    return {
      records,
      groups,
      loading,
      loadError,
      editingId,
      editingGroupId,
      runResults,
      emptyRunGroups,
      cmdlets,
      ops,
      tagSuggestions,
      hasAllRunSummary,
      allRunSummaryText,
      allRunSummaryClass,
      load,
      createRule,
      createFolder,
      onRunAll,
      onEditRule,
      onRunRule,
      onDuplicateRule,
      onDeleteRule,
      onEditGroup,
      onRunGroup,
      onAddRuleToGroup,
      onAddSubfolder,
      onDeleteGroup,
      onSaveRule,
      onCancelEdit,
      onSaveGroup,
      onCancelGroupEdit,
      onReorder,
    };
  },
};

export default QcRulesList;
