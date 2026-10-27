import { computed, ref, onMounted, defineComponent, h } from 'vue';

import RecordsFilter from '../../common_components/records_filter/index';
import { makeFetchResponseErrorMessage } from '../../common_defs/helper_functions';
import logError from '../../common_components/_log_error_proxy';
import { createModal } from '../../common_components/modals/modals';
import RuleRecord from './rule_record';
import RulesTree from './rules_tree';
import RuleForm from './rule_form';
import RuleDeleteConfirm from './rule_delete_confirm';

import './styles.css';

const COLUMNS = {
  name: { label: 'Name', type: 'text', description: 'Display name of the QC rule.' },
  op: { label: 'Operator', type: 'text', description: 'Comparison operator between the left and right chains.' },
  comment: { label: 'Comment', type: 'text', description: 'Short human-readable note about the rule.' },
  tags: { label: 'Tags', type: 'multipunch', description: 'Tags attached to the rule; a rule must have all selected tags.' },
  markers: { label: 'Markers', type: 'multipunch', description: 'Pytest markers that change how the rule runs, e.g. skip or xfail.' },
  created_at: { label: 'Created', type: 'text', description: 'When the rule was created.' },
  modified_at: { label: 'Modified', type: 'text', description: 'When the rule was last modified.' },
};

function toRecord(rule) {
  const meta = rule.meta || {};
  return {
    id: rule.id || '',
    name: rule.name || '',
    group: rule.group || '',
    order: meta.order ?? 0,
    op: rule.op || '',
    comment: meta.comment || '',
    tags: Array.isArray(meta.tags) ? meta.tags.slice() : [],
    created_at: meta.created_at || '',
    modified_at: meta.modified_at || '',
    markers: Array.isArray(meta.markers) ? meta.markers : [],
    left: Array.isArray(rule.left) ? rule.left : [],
    right: Array.isArray(rule.right) ? rule.right : [],
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
    aliases: Array.isArray(group.aliases) ? group.aliases.map(toAlias) : [],
    meta,
  };
}

const QcRulesList = {
  components: {
    'component-records-filter': RecordsFilter,
    'rule-record': RuleRecord,
    'rules-tree': RulesTree,
  },

  template: `
<div class="apqa-qcrules-page">
  <div v-if="loading" class="apqa-qcrules-page-state">Loading QC rules...</div>
  <div v-else-if="loadError" class="apqa-qcrules-page-state apqa-qcrules-page-state-error">{{ loadError }}</div>
  <template v-else>
    <div class="apqa-qcrules-page-toolbar">
      <button type="button" class="apqa-qcrules-page-button apqa-qcrules-page-button-primary" @click="createRule">Create new QC rule</button>
      <button type="button" class="apqa-qcrules-page-button" @click="createGroup">Create group</button>
      <button type="button" class="apqa-qcrules-page-button" @click="createAlias">Add alias</button>
    </div>

    <section class="apqa-qcrules-page-section">
      <h2 class="apqa-qcrules-page-section-title">QC rules</h2>
      <component-records-filter :columns="columns" :records="records" key-field="id" need-sort :records-per-page="0">
        <template #default="{ records: visibleRecords }">
          <rules-tree v-if="visibleRecords.length" :records="visibleRecords" :groups="groups" :records-per-page="25" @edit="onEditRule" @run="onRunRule" @delete="onDeleteRule" />
          <div v-else class="apqa-qcrules-page-empty">No QC rules match the current filter.</div>
        </template>
      </component-records-filter>
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

    // Tags and markers are multi-punch columns, so their allowed values depend
    // on the loaded records. Start from the static column shape and fill in the
    // distinct values as the `options` for the `component-input-multipunch` drop downs.
    const columns = computed(() => {
      const tags = new Set();
      const markers = new Set();
      for (const record of records.value) {
        for (const tag of record.tags) tags.add(tag);
        for (const marker of record.markers) markers.add(marker);
      }
      return {
        ...COLUMNS,
        tags: { ...COLUMNS.tags, options: Array.from(tags).sort() },
        markers: { ...COLUMNS.markers, options: Array.from(markers).sort() },
      };
    });

    const groupNames = computed(() => groups.value.map((group) => group.name).sort().join(', '));

    // Distinct tags across loaded rules, used as suggestions in the create form.
    const tagSuggestions = computed(() => {
      const seen = new Set();
      for (const record of records.value) {
        for (const tag of record.tags) seen.add(tag);
      }
      return Array.from(seen).sort();
    });

    // Resolve a user-typed group reference (display name or id) to the group id
    // stored on rules/groups. Unknown values are passed through for the backend
    // to reject with a clear message.
    function groupIdFor(value) {
      const input = (value || '').trim();
      if (!input) return '';
      const byName = groups.value.find((group) => group.name === input);
      if (byName) return byName.id;
      const byId = groups.value.find((group) => group.id === input);
      if (byId) return byId.id;
      return input;
    }

    async function requestJson(url) {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(await makeFetchResponseErrorMessage(response));
      }
      return response.json();
    }

    async function load() {
      loading.value = true;
      loadError.value = '';
      try {
        const [rulesData, groupsData] = await Promise.all([
          requestJson('/qc/rules'),
          requestJson('/qc/groups'),
        ]);
        records.value = (rulesData.rules || []).map(toRecord);
        groups.value = (groupsData.groups || []).map(toGroupRecord);
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
        cmdletMetadata.value = await requestJson('/functionality/cmdlet-metadata');
      }
      return cmdletMetadata.value;
    }

    async function createRule() {
      let metadata;
      try {
        metadata = await ensureCmdletMetadata();
      } catch (e) {
        window.alert(`Failed to load cmdlet metadata: ${e}`);
        logError(`Failed to load cmdlet metadata: ${e}`);
        return;
      }

      const MyForm = defineComponent({
        setup: (_, { attrs }) => () =>
          h(RuleForm, {
            ...attrs,
            cmdlets: metadata.cmdlets || [],
            ops: metadata.ops || [],
            tagSuggestions: tagSuggestions.value,
          }),
      });

      let payload;
      try {
        payload = await createModal(MyForm);
      } catch (e) {
        // Modal dismissed — nothing to create.
        return;
      }

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

      try {
        await postJson('/qc/rules', payload);
        await load();
      } catch (e) {
        window.alert(`Failed to create QC rule: ${e}`);
        logError(`Failed to create QC rule: ${e}`);
      }
    }

    async function createGroup() {
      const name = window.prompt('New group name');
      if (name == null || name.trim() === '') return;
      let parent = '';
      if (groups.value.length) {
        const answer = window.prompt(
          `Parent group for "${name.trim()}"? (leave empty for top-level)\nExisting groups: ${groupNames.value}`,
          '',
        );
        if (answer == null) return;
        parent = groupIdFor(answer);
      }
      try {
        await postJson('/qc/groups', { name: name.trim(), parent });
        await load();
      } catch (e) {
        window.alert(`Failed to create group: ${e}`);
        logError(`Failed to create group: ${e}`);
      }
    }

    async function createAlias() {
      const groupName = window.prompt(
        `Folder (group) to add the alias to.\nExisting groups: ${groupNames.value}`,
      );
      if (groupName == null || groupName.trim() === '') return;
      const group = groups.value.find(
        (g) => g.name === groupName.trim() || g.id === groupName.trim(),
      );
      if (!group) {
        window.alert(`Group not found: ${groupName.trim()}`);
        return;
      }
      const name = window.prompt('Alias name');
      if (name == null || name.trim() === '') return;
      const chainText = window.prompt(
        'Cmdlet chain as a JSON array of {cmdlet, args} objects',
        '[{"cmdlet":"get-content-mdd","args":{"path":"s:\\\\..."}}]',
      );
      if (chainText == null) return;
      let chain;
      try {
        chain = JSON.parse(chainText);
      } catch (e) {
        window.alert(`Failed to parse cmdlet chain: ${e}`);
        return;
      }
      if (!Array.isArray(chain)) {
        window.alert('Cmdlet chain must be a JSON array');
        return;
      }
      const aliases = group.aliases.filter((alias) => alias.name !== name.trim());
      aliases.push({ name: name.trim(), chain });
      try {
        await putJson(`/qc/groups/${encodeURIComponent(group.id)}`, { aliases });
        await load();
      } catch (e) {
        window.alert(`Failed to add alias: ${e}`);
        logError(`Failed to add alias: ${e}`);
      }
    }

    // Placeholders for the rule actions. The edit/run UI is a separate roadmap
    // item; for now the buttons just surface the selected rule to the console.
    function onEditRule(record) {
      // TODO(roadmap): open the rule editor once the CRUD UI is implemented.
      console.debug('edit rule (not implemented yet):', record.name);
    }

    function onRunRule(record) {
      // TODO(roadmap): run the rule once the runner UI is implemented.
      console.debug('run rule (not implemented yet):', record.name);
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
        await load();
      } catch (e) {
        window.alert(`Failed to delete QC rule: ${e}`);
        logError(`Failed to delete QC rule: ${e}`);
      }
    }

    onMounted(load);

    return {
      columns,
      records,
      groups,
      loading,
      loadError,
      load,
      createRule,
      createGroup,
      createAlias,
      onEditRule,
      onRunRule,
      onDeleteRule,
    };
  },
};

export default QcRulesList;
