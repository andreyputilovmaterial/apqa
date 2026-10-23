import { computed, onBeforeUnmount, onMounted, ref } from 'vue';

import './styles.css';

// Global multi-punch (multi-select) drop down.
//
// Renders a single-line trigger that opens a list of checkable options on
// click. Clicking outside the component closes the drop down. The value is an
// array of the selected option values, suitable for `v-model`.
//
// `options` may be a plain array of strings/numbers, or an array of
// `{ value, label }` objects. When only one of `value`/`label` is given for an
// object option, the other falls back to the same value.
const Multipunch = {
  inheritAttrs: false,

  props: {
    modelValue: { type: Array, default: () => [] },
    options: { type: Array, default: () => [] },
    placeholder: { type: String, default: '' },
    name: { type: String, default: '' },
  },

  emits: ['update:modelValue', 'change'],

  template: `
<div ref="rootEl" class="apqa-multipunch">
  <button
    type="button"
    class="apqa-multipunch-trigger"
    :aria-expanded="String(open)"
    aria-haspopup="listbox"
    @click="toggle"
  >
    <span
      class="apqa-multipunch-trigger-value"
      :class="{ 'is-placeholder': !summaryText }"
    >{{ summaryText || placeholder }}</span>
    <span class="apqa-multipunch-trigger-caret" aria-hidden="true">▾</span>
  </button>

  <div v-if="open" class="apqa-multipunch-menu" role="listbox" aria-multiselectable="true">
    <label v-for="option in options" :key="optionKey(option)" class="apqa-multipunch-option">
      <input
        type="checkbox"
        :name="name"
        :value="optionValue(option)"
        :checked="isChecked(option)"
        @change="toggleOption(option, $event.target.checked)"
      />
      <span class="apqa-multipunch-option-label">{{ optionLabel(option) }}</span>
    </label>
  </div>
</div>
`,

  setup(props, { emit }) {
    const rootEl = ref(null);
    const open = ref(false);

    const valueSet = computed(() => new Set((props.modelValue || []).map(String)));

    const summaryText = computed(() => {
      const selected = (props.modelValue || []).filter((v) => v != null);
      return selected.map((v) => optionLabelForValue(v)).join(', ');
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

    function isChecked(option) {
      return valueSet.value.has(String(optionValue(option)));
    }

    function toggle() {
      open.value = !open.value;
    }

    function close() {
      open.value = false;
    }

    function toggleOption(option, checked) {
      const value = optionValue(option);
      const next = (props.modelValue || []).filter((v) => String(v) !== String(value));
      if (checked) next.push(value);
      emit('update:modelValue', next);
      emit('change', next);
    }

    function onDocumentPointerDown(event) {
      if (rootEl.value && !rootEl.value.contains(event.target)) close();
    }

    onMounted(() => document.addEventListener('pointerdown', onDocumentPointerDown));
    onBeforeUnmount(() => document.removeEventListener('pointerdown', onDocumentPointerDown));

    return {
      rootEl,
      open,
      summaryText,
      toggle,
      close,
      toggleOption,
      isChecked,
      optionKey,
      optionValue,
      optionLabel,
    };
  },
};

export default Multipunch;
