import { computed, ref, onMounted } from 'vue';

import RecordsFilter from '../../common_components/records_filter/index';
import { makeFetchResponseErrorMessage } from '../../common_defs/helper_functions';
import logError from '../../common_components/_log_error_proxy';
import Rule from './rule';

import './styles.css';

const COLUMNS = {
  name: { label: 'Name', type: 'text' },
  op: { label: 'Operator', type: 'text' },
  comment: { label: 'Comment', type: 'text' },
  tags: { label: 'Tags', type: 'multipunch' },
  created_at: { label: 'Created', type: 'text' },
  modified_at: { label: 'Modified', type: 'text' },
};

function toRecord(rule) {
  const meta = rule.meta || {};
  return {
    id: rule.name,
    name: rule.name,
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

const ProjectsList = {
  components: {
    'component-records-filter': RecordsFilter,
    'rule': Rule,
  },

  template: `
<div class="apqa-projects-list">
  <div v-if="loading" class="apqa-projects-list-state">Loading QC rules...</div>
  <div v-else-if="loadError" class="apqa-projects-list-state apqa-projects-list-state-error">{{ loadError }}</div>
  <component-records-filter
    v-else
    :columns="columns"
    :records="records"
    key-field="id"
    need-sort
  >
    <template #default="{ records: visibleRecords }">
      <ul v-if="visibleRecords.length" class="apqa-projects-list-items">
        <rule v-for="record in visibleRecords" :key="record.id" :record="record" />
      </ul>
      <div v-else class="apqa-projects-list-state apqa-projects-list-empty">No QC rules match the current filter.</div>
    </template>
  </component-records-filter>
</div>
`,

  setup() {
    const records = ref([]);
    const loading = ref(true);
    const loadError = ref('');

    // Tags are a multi-punch column, so their allowed values depend on the
    // loaded records. Start from the static column shape and fill in the
    // distinct tag values as the `options` for the `component-multipunch`
    // drop down.
    const columns = computed(() => {
      const tags = new Set();
      for (const record of records.value) {
        for (const tag of record.tags) tags.add(tag);
      }
      return {
        ...COLUMNS,
        tags: { ...COLUMNS.tags, options: Array.from(tags).sort() },
      };
    });

    async function load() {
      loading.value = true;
      loadError.value = '';
      try {
        const response = await fetch('/qcrules');
        if (!response.ok) {
          throw new Error(await makeFetchResponseErrorMessage(response));
        }
        const data = await response.json();
        records.value = (data.rules || []).map(toRecord);
      } catch (e) {
        loadError.value = `Failed to load QC rules: ${e}`;
        logError(loadError.value);
      } finally {
        loading.value = false;
      }
    }

    onMounted(load);

    return {
      columns,
      records,
      loading,
      loadError,
      load,
    };
  },
};

export default ProjectsList;
