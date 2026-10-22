import { ref, onMounted } from 'vue';

import RecordsFilter from '../../common_components/records_filter/index';
import { makeFetchResponseErrorMessage } from '../../common_defs/helper_functions';

import './styles.css';

const COLUMNS = {
  name: { label: 'Name', type: 'text' },
  op: { label: 'Operator', type: 'text' },
  enabled: { label: 'Enabled', type: 'text' },
  comment: { label: 'Comment', type: 'text' },
  tags: { label: 'Tags', type: 'text' },
  created_at: { label: 'Created', type: 'text' },
  modified_at: { label: 'Modified', type: 'text' },
};

function formatCmdlet(cmdlet) {
  const name = cmdlet?.cmdlet || '';
  const args = cmdlet?.args || {};
  const parts = [name];
  for (const [key, value] of Object.entries(args)) {
    if (value === true) parts.push(key);
    else if (value == null || value === false) parts.push(`${key}=${value}`);
    else if (typeof value === 'object') parts.push(`${key}=${JSON.stringify(value)}`);
    else parts.push(`${key}=${String(value)}`);
  }
  return parts.join(' ');
}

function formatChain(chain) {
  return (Array.isArray(chain) ? chain : []).map(formatCmdlet).join(' | ');
}

function toRecord(rule) {
  const meta = rule.meta || {};
  const enabled = meta.enabled === true ? 'yes' : (meta.enabled === false ? 'no' : '');
  return {
    id: rule.name,
    name: rule.name,
    op: rule.op || '',
    enabled,
    comment: meta.comment || '',
    tags: Array.isArray(meta.tags) ? meta.tags.join(', ') : '',
    created_at: meta.created_at || '',
    modified_at: meta.modified_at || '',
    markers: Array.isArray(meta.markers) ? meta.markers : [],
    leftText: formatChain(rule.left),
    rightText: formatChain(rule.right),
  };
}

const ProjectsList = {
  props: ['repoActions'],

  components: {
    'component-records-filter': RecordsFilter,
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
        <li
          v-for="record in visibleRecords"
          :key="record.id"
          class="apqa-projects-list-item"
          :class="record._filterMeta.cssClasses"
        >
          <div class="apqa-projects-list-item-head">
            <span class="apqa-projects-list-item-name">{{ record.name }}</span>
            <span v-if="record.op" class="apqa-projects-list-item-op">{{ record.op }}</span>
            <span
              v-if="record.enabled"
              class="apqa-projects-list-item-enabled"
              :class="{ 'is-disabled': record.enabled === 'no' }"
            >{{ record.enabled === 'yes' ? 'enabled' : 'disabled' }}</span>
          </div>
          <div v-if="record.comment" class="apqa-projects-list-item-comment">{{ record.comment }}</div>
          <div class="apqa-projects-list-item-definition">
            <code class="apqa-projects-list-item-chain">{{ record.leftText || '(empty)' }}</code>
            <span class="apqa-projects-list-item-definition-op">{{ record.op || '?' }}</span>
            <code class="apqa-projects-list-item-chain">{{ record.rightText || '(empty)' }}</code>
          </div>
          <div v-if="record.markers.length" class="apqa-projects-list-item-markers">
            <span v-for="marker in record.markers" :key="marker" class="apqa-projects-list-item-marker">{{ marker }}</span>
          </div>
          <div class="apqa-projects-list-item-meta">
            <span v-if="record.tags" class="apqa-projects-list-item-tags">{{ record.tags }}</span>
            <span v-if="record.created_at" class="apqa-projects-list-item-created">created {{ record.created_at }}</span>
          </div>
        </li>
      </ul>
      <div v-else class="apqa-projects-list-state apqa-projects-list-empty">No QC rules match the current filter.</div>
    </template>
  </component-records-filter>
</div>
`,

  setup(props) {
    const records = ref([]);
    const loading = ref(true);
    const loadError = ref('');

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
        if (props.repoActions?.logError) props.repoActions.logError(loadError.value);
      } finally {
        loading.value = false;
      }
    }

    onMounted(load);

    return {
      columns: COLUMNS,
      records,
      loading,
      loadError,
      load,
    };
  },
};

export default ProjectsList;
