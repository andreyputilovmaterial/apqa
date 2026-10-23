import { computed, ref, onMounted } from 'vue';

import RecordsFilter from '../../common_components/records_filter/index';
import { makeFetchResponseErrorMessage } from '../../common_defs/helper_functions';
import logError from '../../common_components/_log_error_proxy';
import Rule from './rule';

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

const QcRulesList = {
  components: {
    'component-records-filter': RecordsFilter,
    'rule': Rule,
  },

  template: `
<div class="apqa-qcrules-list">
  <div v-if="loading" class="apqa-qcrules-list-state">Loading QC rules...</div>
  <div v-else-if="loadError" class="apqa-qcrules-list-state apqa-qcrules-list-state-error">{{ loadError }}</div>
  <component-records-filter
    v-else
    :columns="columns"
    :records="records"
    key-field="id"
    need-sort
  >
    <template #default="{ records: visibleRecords }">
      <ul v-if="visibleRecords.length" class="apqa-qcrules-list-items">
        <rule v-for="record in visibleRecords" :key="record.id" :record="record" />
      </ul>
      <div v-else class="apqa-qcrules-list-state apqa-qcrules-list-empty">No QC rules match the current filter.</div>
    </template>
  </component-records-filter>
</div>
`,

  setup() {
    const records = ref([]);
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

export default QcRulesList;
