import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';

import './styles.css';

// Single-select drop down with a search box, focused by default when the menu
// opens. It only allows choosing from the pre-defined `options` list (no
// free-form value), like a native <select>, but typing in the search box filters
// the list for quick selection.
//
// The value is a single option value (string or number), suitable for `v-model`,
// and it follows the native input contract (update:modelValue + change/input).
//
// `options` may be a plain array of strings/numbers, or an array of
// `{ value, label }` objects. When only one of `value`/`label` is given for an
// object option, the other falls back to the same value.
const InputSearchSelect = {
  inheritAttrs: false,

  props: {
    modelValue: { type: [String, Number], default: null },
    options: { type: Array, default: () => [] },
    placeholder: { type: String, default: '' },
    name: { type: String, default: '' },
  },

  emits: ['update:modelValue', 'change', 'input'],

  template: `
<div ref="rootEl" class="apqa-input-search-select">
  <button
    type="button"
    class="apqa-input-search-select-trigger"
    :aria-expanded="String(open)"
    aria-haspopup="listbox"
    @click="toggle"
  >
    <span
      class="apqa-input-search-select-trigger-value"
      :class="{ 'is-placeholder': !selectedLabel }"
    >{{ selectedLabel || placeholder }}</span>
    <span class="apqa-input-search-select-trigger-caret" aria-hidden="true">▾</span>
  </button>

  <input v-if="modelValue != null" type="hidden" :name="name" :value="modelValue" />

  <div v-if="open" class="apqa-input-search-select-menu">
    <input
      ref="searchEl"
      type="text"
      class="apqa-input-search-select-search"
      :placeholder="placeholder"
      v-model="query"
      @keydown="onKeydown"
    />
    <div class="apqa-input-search-select-list" role="listbox">
      <button
        v-for="(option, index) in filtered"
        :key="optionKey(option)"
        type="button"
        class="apqa-input-search-select-option"
        :class="{ 'is-highlighted': index === highlight }"
        role="option"
        :aria-selected="String(isSelected(option))"
        @click="select(option)"
        @mouseenter="setHighlight(index)"
      >
        {{ optionLabel(option) }}
      </button>
      <div v-if="!filtered.length" class="apqa-input-search-select-empty">No matches</div>
    </div>
  </div>
</div>
`,

  setup(props, { emit }) {
    const rootEl = ref(null);
    const searchEl = ref(null);
    const open = ref(false);
    const query = ref('');
    const highlight = ref(0);

    const filtered = computed(() => {
      const q = query.value.trim().toLowerCase();
      if (!q) return props.options || [];
      return (props.options || []).filter((option) =>
        optionLabel(option).toLowerCase().includes(q),
      );
    });

    const selectedLabel = computed(() => {
      const value = props.modelValue;
      if (value == null || value === '') return '';
      return optionLabelForValue(value);
    });

    function optionKey(option) {
      return typeof option === 'object' && option !== null
        ? String(option.value ?? option.label ?? '')
        : String(option);
    }

    function optionValue(option) {
      return typeof option === 'object' && option !== null
        ? (option.value ?? option.label)
        : option;
    }

    function optionLabel(option) {
      return typeof option === 'object' && option !== null
        ? (option.label ?? option.value ?? '')
        : String(option);
    }

    function optionLabelForValue(value) {
      const option = (props.options || []).find(
        (o) => String(optionValue(o)) === String(value),
      );
      return option ? optionLabel(option) : String(value);
    }

    function isSelected(option) {
      const value = props.modelValue;
      if (value == null || value === '') return false;
      return String(value) === String(optionValue(option));
    }

    async function openMenu() {
      query.value = '';
      highlight.value = 0;
      open.value = true;
      await nextTick();
      searchEl.value?.focus();
    }

    function close() {
      open.value = false;
    }

    async function toggle() {
      if (open.value) close();
      else await openMenu();
    }

    function select(option) {
      const value = optionValue(option);
      emit('update:modelValue', value);
      emit('change', value);
      emit('input', value);
      close();
    }

    function setHighlight(index) {
      highlight.value = index;
    }

    function onKeydown(event) {
      if (event.key === 'Escape') {
        close();
        return;
      }
      if (event.key === 'ArrowDown') {
        event.preventDefault();
        highlight.value = Math.min(highlight.value + 1, filtered.value.length - 1);
        return;
      }
      if (event.key === 'ArrowUp') {
        event.preventDefault();
        highlight.value = Math.max(highlight.value - 1, 0);
        return;
      }
      if (event.key === 'Enter') {
        event.preventDefault();
        const option = filtered.value[highlight.value];
        if (option != null) select(option);
      }
    }

    // Reset the highlighted entry whenever the filtered list changes (e.g. on
    // every keystroke), so Enter/arrow navigation stays predictable.
    watch(filtered, () => {
      highlight.value = 0;
    });

    function onDocumentPointerDown(event) {
      if (rootEl.value && !rootEl.value.contains(event.target)) close();
    }

    onMounted(() => document.addEventListener('pointerdown', onDocumentPointerDown));
    onBeforeUnmount(() => document.removeEventListener('pointerdown', onDocumentPointerDown));

    return {
      rootEl,
      searchEl,
      open,
      query,
      highlight,
      filtered,
      selectedLabel,
      toggle,
      close,
      select,
      setHighlight,
      onKeydown,
      optionKey,
      optionLabel,
      isSelected,
    };
  },
};

export default InputSearchSelect;
