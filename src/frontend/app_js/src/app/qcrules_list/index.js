import { computed, ref, onMounted } from 'vue';

import RecordsFilter from '../../common_components/records_filter/index';
import { makeFetchResponseErrorMessage } from '../../common_defs/helper_functions';
import logError from '../../common_components/_log_error_proxy';
import DefinitionRecord from './definition_record';
import RuleRecord from './rule_record';
import RulesTree from './rules_tree';

import './styles.css';

const COLUMNS = {
  name: { label: 'Name', type: 'text', description: 'Unique QC rule name.' },
  op: { label: 'Operator', type: 'text', description: 'Comparison operator between the left and right chains.' },
  comment: { label: 'Comment', type: 'text', description: 'Short human-readable note about the rule.' },
  tags: { label: 'Tags', type: 'multipunch', description: 'Tags attached to the rule; a rule must have all selected tags.' },
  markers: { label: 'Markers', type: 'multipunch', description: 'Pytest markers that change how the rule runs, e.g. skip or xfail.' },
  created_at: { label: 'Created', type: 'text', description: 'When the rule was created.' },
  modified_at: { label: 'Modified', type: 'text', description: 'When the rule was last modified.' },
};

const DEFINITION_COLUMNS = {
  name: { label: 'Name', type: 'text', description: 'Unique alias name.' },
  value: { label: 'Value', type: 'text', description: 'Value the alias resolves to (e.g. a path).' },
  comment: { label: 'Comment', type: 'text', description: 'Short human-readable note about the alias.' },
};

function toRecord(rule) {
  const meta = rule.meta || {};
  return {
    id: rule.name,
    name: rule.name,
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

function toDefinitionRecord(definition) {
  const meta = definition.meta || {};
  return {
    id: definition.name,
    name: definition.name,
    value: definition.value || '',
    comment: meta.comment || '',
  };
}

function toGroupRecord(group) {
  const meta = group.meta || {};
  return {
    id: group.name,
    name: group.name,
    parent: group.parent || '',
    order: meta.order ?? 0,
    meta,
  };
}

const QcRulesList = {
  components: {
    'component-records-filter': RecordsFilter,
    'definition-record': DefinitionRecord,
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
      <button type="button" class="apqa-qcrules-page-button" @click="createDefinition">Add alias</button>
    </div>

    <section class="apqa-qcrules-page-section">
      <h2 class="apqa-qcrules-page-section-title">Global aliases</h2>
      <component-records-filter :columns="definitionColumns" :records="definitions" key-field="id" :records-per-page="0">
        <template #default="{ records: visibleDefinitions }">
          <ul v-if="visibleDefinitions.length" class="apqa-qcrules-definition-list">
            <definition-record v-for="definition in visibleDefinitions" :key="definition.id" :record="definition" />
          </ul>
          <div v-else class="apqa-qcrules-page-empty">No aliases defined.</div>
        </template>
      </component-records-filter>
    </section>

    <section class="apqa-qcrules-page-section">
      <h2 class="apqa-qcrules-page-section-title">QC rules</h2>
      <component-records-filter :columns="columns" :records="records" key-field="id" need-sort :records-per-page="0">
        <template #default="{ records: visibleRecords }">
          <rules-tree v-if="visibleRecords.length" :records="visibleRecords" :groups="groups" :records-per-page="25" @edit="onEditRule" @run="onRunRule" />
          <div v-else class="apqa-qcrules-page-empty">No QC rules match the current filter.</div>
        </template>
      </component-records-filter>
    </section>
  </template>
</div>
`,

  setup() {
    const records = ref([]);
    const definitions = ref([]);
    const groups = ref([]);
    const loading = ref(true);
    const loadError = ref('');

    // Tags and markers are multi-punch columns, so their allowed values depend
    // on the loaded records. Start from the static column shape and fill in the
    // distinct values as the `options` for the `component-multipunch` drop downs.
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

    const definitionColumns = computed(() => DEFINITION_COLUMNS);

    const groupNames = computed(() => groups.value.map((group) => group.name).sort().join(', '));

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
        const [rulesData, definitionsData, groupsData] = await Promise.all([
          requestJson('/qc/rules'),
          requestJson('/qc/definitions'),
          requestJson('/qc/groups'),
        ]);
        records.value = (rulesData.rules || []).map(toRecord);
        definitions.value = (definitionsData.definitions || []).map(toDefinitionRecord);
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

    async function createRule() {
      const name = window.prompt('New QC rule name');
      if (name == null || name.trim() === '') return;
      let group = '';
      if (groups.value.length) {
        const answer = window.prompt(
          `Group for "${name.trim()}"? (leave empty for none)\nExisting groups: ${groupNames.value}`,
          '',
        );
        if (answer == null) return;
        group = answer.trim();
      }
      try {
        await postJson('/qc/rules', { name: name.trim(), group });
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
        parent = answer.trim();
      }
      try {
        await postJson('/qc/groups', { name: name.trim(), parent });
        await load();
      } catch (e) {
        window.alert(`Failed to create group: ${e}`);
        logError(`Failed to create group: ${e}`);
      }
    }

    async function createDefinition() {
      const name = window.prompt('New alias name');
      if (name == null || name.trim() === '') return;
      const value = window.prompt('Alias value (e.g. a path)');
      if (value == null) return;
      try {
        await postJson('/qc/definitions', { name: name.trim(), value });
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

    onMounted(load);

    return {
      columns,
      definitionColumns,
      records,
      definitions,
      groups,
      loading,
      loadError,
      load,
      createRule,
      createGroup,
      createDefinition,
      onEditRule,
      onRunRule,
    };
  },
};

export default QcRulesList;
