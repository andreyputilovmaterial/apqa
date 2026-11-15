import { computed, ref, watch } from 'vue';

import InputArgText from '../text/index';
import InputArgNumber from '../number/index';
import InputArgBoolean from '../boolean/index';
import InputArgPath from '../path/index';
import InputArgDate from '../date/index';
import InputArgJson from '../json/index';

import './styles.css';

// Map a stored value to the literal type that best describes it, so existing
// rules (whose `value` is any JSON scalar/array/object) open in the right editor.
function detectType(value) {
  if (value === null || value === undefined) return 'text';
  if (typeof value === 'boolean') return 'boolean';
  if (typeof value === 'number') return 'number';
  if (typeof value === 'string') return 'text';
  return 'json'; // array or object
}

// Convert the current value when the user switches type. Rules are explicit and
// predictable: text stringifies, number parses a numeric value (else blank
// `sysmissing`), boolean keeps a boolean (else `false`), json keeps the value.
function coerceTo(type, value) {
  switch (type) {
    case 'boolean':
      return typeof value === 'boolean' ? value : false;
    case 'number':
      if (typeof value === 'number') return value;
      if (typeof value === 'string' && value.trim() !== '' && !Number.isNaN(Number(value))) {
        return Number(value);
      }
      return null; // blank number → sysmissing
    case 'json':
      return value === undefined ? null : value;
    case 'path':
    case 'date':
      if (value === null || value === undefined) return null;
      return typeof value === 'object' ? JSON.stringify(value) : String(value);
    case 'text':
    default:
      if (value === null || value === undefined) return '';
      if (typeof value === 'object') return JSON.stringify(value);
      return String(value);
  }
}

const TYPE_OPTIONS = [
  { value: 'text', label: 'text' },
  { value: 'number', label: 'number' },
  { value: 'boolean', label: 'boolean' },
  { value: 'path', label: 'path' },
  { value: 'date', label: 'date' },
  { value: 'json', label: 'json' },
];

const EDITORS = {
  text: InputArgText,
  number: InputArgNumber,
  boolean: InputArgBoolean,
  path: InputArgPath,
  date: InputArgDate,
  json: InputArgJson,
};

// `literal-value` arg editor: an explicit type selector plus the matching typed
// input, so a literal is unambiguously text / number / boolean / json instead of
// guessing from raw JSON syntax. The stored `args.value` stays a single JSON
// value (no separate type field), so existing rules keep working; the selected
// type is a view over that value — inferred on open and coerced when changed.
const InputArgLiteralValue = {
  inheritAttrs: false,

  props: {
    value: { default: undefined },
    name: { type: String, default: '' },
  },

  emits: ['update:value'],

  setup(props, { emit }) {
    const selectedType = ref(detectType(props.value));
    // Set on the emit that follows our own edit, so the watcher below does not
    // re-infer the type (and yank the selector) from a coerced/blank value.
    let internal = false;

    const childComponent = computed(() => EDITORS[selectedType.value] || InputArgText);

    watch(
      () => props.value,
      (value) => {
        if (internal) {
          internal = false;
          return;
        }
        selectedType.value = detectType(value);
      },
      { immediate: true },
    );

    function emitValue(value) {
      internal = true;
      emit('update:value', value);
    }

    function onTypeChange(event) {
      selectedType.value = event.target.value;
      emitValue(coerceTo(selectedType.value, props.value));
    }

    function onChildUpdate(value) {
      emitValue(value);
    }

    return { selectedType, TYPE_OPTIONS, childComponent, onTypeChange, onChildUpdate };
  },

  template: `
<div class="apqa-input-literal-value">
  <select
    class="apqa-input-cmdlet-arg-input apqa-input-literal-value-type"
    :value="selectedType"
    @change="onTypeChange"
  >
    <option v-for="o in TYPE_OPTIONS" :key="o.value" :value="o.value">{{ o.label }}</option>
  </select>
  <div class="apqa-input-literal-value-editor">
    <component :is="childComponent" :value="value" :name="name" @update:value="onChildUpdate" />
  </div>
</div>
`,
};

export default InputArgLiteralValue;
