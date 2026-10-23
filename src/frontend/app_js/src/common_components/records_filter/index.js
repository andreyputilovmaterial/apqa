import { computed, reactive, ref, watch } from 'vue';

import { compareValues, matchesRecord, summarizeFilters } from './matchers';

import './styles.css';

// How long a record that became hidden stays mounted (css-hidden) before being
// dropped from the rendered list. Preserves component state while the user
// types quickly into the filter boxes.
const HIDE_TTL_MS = 5 * 60 * 1000;

const RecordsFilter = {
  props: {
    columns: { type: Object, required: true },
    records: { type: Array, required: true },
    keyField: { type: String, required: true },
    needSort: { type: Boolean, default: false },
    recordsPerPage: { type: Number, default: 25 },
  },

  template: `
<div class="apqa-records-filter">
  <button
    type="button"
    class="apqa-records-filter-header"
    :aria-expanded="String(!collapsed)"
    @click="collapsed = !collapsed"
  >
    <span class="apqa-records-filter-header-toggle" aria-hidden="true">{{ collapsed ? '▸' : '▾' }}</span>
    <span class="apqa-records-filter-header-label">Filter</span>
    <span v-if="filterSummaryText" class="apqa-records-filter-header-summary">{{ filterSummaryText }}</span>
  </button>

  <form v-if="!collapsed" class="apqa-records-filter-form" @submit.prevent>
    <div class="apqa-records-filter-fields">
      <label v-for="(def, key) in columnsSanitized" :key="key" class="apqa-records-filter-field">
        <span class="apqa-records-filter-field-label">{{ def.label }}</span>
        <component
          v-if="isRangeType(def.type)"
          :is="def.type === 'number' ? 'component-input-numericrange' : 'component-input-datetimerange'"
          v-model="filters[key]"
          :name="'filter-' + key"
          :placeholder="'Filter ' + def.label.toLowerCase() + '...'"
        />
        <input
          v-else
          v-model="filters[key]"
          type="text"
          :name="'filter-' + key"
          class="apqa-records-filter-field-input"
          :placeholder="'Filter ' + def.label.toLowerCase() + '...'"
        />
      </label>
    </div>
  </form>

  <div v-if="!collapsed" class="apqa-records-filter-toolbar">
    <label class="apqa-records-filter-sort">
      <span class="apqa-records-filter-sort-label">Sort by</span>
      <select v-model="sortingColumn" name="sort-column" class="apqa-records-filter-select">
        <option value="">not sorted</option>
        <option v-for="(def, key) in columnsSanitized" :key="key" :value="key">{{ def.label }}</option>
      </select>
      <select v-model="sortingAscending" name="sort-order" class="apqa-records-filter-select">
        <option :value="true">ascending</option>
        <option :value="false">descending</option>
      </select>
    </label>

    <div v-if="numPages > 1" class="apqa-records-filter-pagination">
      <span class="apqa-records-filter-pagination-label">Page</span>
      <button
        v-for="n in numPages"
        :key="n"
        type="button"
        class="apqa-records-filter-page"
        :class="{ 'is-active': n - 1 === page }"
        @click="selectPage(n - 1)"
      >
        {{ n }}
      </button>
    </div>
  </div>

  <div class="apqa-records-filter-content">
    <slot :records="view" />
  </div>
</div>
`,

  setup(props) {
    const columnsSanitized = computed(() => {
      const out = {};
      for (const [key, def] of Object.entries(props.columns)) {
        if (typeof def === 'string') out[key] = { type: 'text', label: def };
        else if (def && typeof def === 'object') out[key] = { type: def.type || 'text', label: def.label || key };
        else out[key] = { type: 'text', label: key };
      }
      return out;
    });

    const filters = reactive({});
    for (const key of Object.keys(props.columns)) filters[key] = '';

    const sortingColumn = ref('');
    const sortingAscending = ref(true);
    const page = ref(0);

    // Collapsed = one-line header with a summary of active filters; expanded =
    // the full set of filter boxes plus the sort/pagination toolbar.
    const collapsed = ref(true);
    const filterSummaryText = computed(() =>
      summarizeFilters(filters, columnsSanitized.value).join(' · '),
    );

    const perPage = computed(() => {
      if (props.recordsPerPage === 0) return props.records.length || 1;
      return props.recordsPerPage > 0 ? props.recordsPerPage : 25;
    });

    function recordMatches(record) {
      return matchesRecord(record, filters, columnsSanitized.value);
    }

    function isRangeType(type) {
      return type === 'number' || type === 'date' || type === 'datetime';
    }

    const matchedCount = computed(() => props.records.filter((record) => recordMatches(record)).length);
    const numPages = computed(() => Math.max(1, Math.ceil(matchedCount.value / perPage.value)));

    watch(numPages, (n) => {
      if (page.value >= n) page.value = 0;
    });

    function selectPage(index) {
      page.value = index;
    }

    // Persisted per-record bookkeeping. Intentionally not reactive — it is only a
    // cache of "last hidden" timestamps; the reactive `view` below drives rendering.
    const meta = new Map();

    const view = computed(() => {
      const cols = columnsSanitized.value;
      const now = Date.now();
      const pageStart = page.value * perPage.value;
      const pageEnd = pageStart + perPage.value;

      const list = props.records.slice();
      if (props.needSort && sortingColumn.value && cols[sortingColumn.value]) {
        list.sort((a, b) =>
          compareValues(
            a[sortingColumn.value],
            b[sortingColumn.value],
            cols[sortingColumn.value].type,
            sortingAscending.value,
          ),
        );
      }

      // 1) filter: mark non-matching records as hidden
      for (const record of list) {
        const key = record[props.keyField];
        let m = meta.get(key);
        if (!m) {
          m = { wasEverShown: false, prevIsHidden: false, isHidden: false, lastHiddenAt: 0 };
          meta.set(key, m);
        }
        m.prevIsHidden = m.isHidden;
        m.isHidden = !recordMatches(record);
      }

      // 2) paginate: hide matching records outside the current page
      let matched = 0;
      for (const record of list) {
        const m = meta.get(record[props.keyField]);
        if (!m.isHidden) {
          if (matched < pageStart || matched >= pageEnd) m.isHidden = true;
          matched++;
        }
      }

      // 3) build the rendered list, keeping recently-hidden records mounted
      const out = [];
      for (const record of list) {
        const m = meta.get(record[props.keyField]);
        if (!m.isHidden) {
          m.wasEverShown = true;
          m.lastHiddenAt = 0;
          out.push({ ...record, _filterMeta: { hidden: false, cssClasses: [] } });
        } else {
          if (!m.prevIsHidden) m.lastHiddenAt = now;
          if (m.wasEverShown && now - m.lastHiddenAt < HIDE_TTL_MS) {
            out.push({ ...record, _filterMeta: { hidden: true, cssClasses: ['apqa-u-hidden'] } });
          }
        }
      }

      return out;
    });

    return {
      columnsSanitized,
      filters,
      sortingColumn,
      sortingAscending,
      page,
      numPages,
      selectPage,
      isRangeType,
      collapsed,
      filterSummaryText,
      view,
    };
  },
};

export default RecordsFilter;
