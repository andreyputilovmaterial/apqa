import { computed, ref, watch } from 'vue';

import InputArgText from '../text/index';
import InputArgNumber from '../number/index';
import InputArgBoolean from '../boolean/index';
import InputArgPath from '../path/index';
import InputArgDate from '../date/index';
import InputArgJson from '../json/index';

import './styles.css';

// A literal `value` arg is stored as a **typed** wrapper — `{ type, value }`, or
// `{ type: 'sysmissing' }` — so the chosen type survives a save/reopen round trip
// (a bare JSON string would otherwise reload as "text"). Rules written before the
// typed form still carry a bare JSON value, which is inferred on open.
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

function isTyped(value) {
  return value !== null && typeof value === 'object' && typeof value.type === 'string';
}

function rawValueOf(value) {
  if (!isTyped(value)) return value;
  return value.type === 'sysmissing' ? null : value.value;
}

function storedTypeToUi(type) {
  switch (type) {
    case 'integer':
    case 'real':
      return 'number';
    case 'block':
    case 'collection':
      return 'json';
    case 'sysmissing':
      return 'text';
    default:
      return type;
  }
}

function uiTypeToStored(uiType, raw) {
  switch (uiType) {
    case 'number':
      return typeof raw === 'number' && Number.isInteger(raw) ? 'integer' : 'real';
    case 'json':
      return Array.isArray(raw) ? 'collection' : 'block';
    case 'boolean':
    case 'path':
    case 'date':
    case 'text':
    default:
      return uiType || 'text';
  }
}

function wrap(uiType, raw) {
  if (raw === null || raw === undefined) return { type: 'sysmissing' };
  return { type: uiTypeToStored(uiType, raw), value: raw };
}

// Infer the UI type from a bare (pre-typed-form) JSON value, so old rules open
// in the right editor.
function detectType(value) {
  if (value === null || value === undefined) return 'text';
  if (typeof value === 'boolean') return 'boolean';
  if (typeof value === 'number') return 'number';
  if (typeof value === 'string') return 'text';
  return 'json'; // array or object
}

function uiTypeOf(value) {
  return isTyped(value) ? storedTypeToUi(value.type) : detectType(value);
}

// Convert the current raw value when the user switches type.
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

const InputArgLiteralValue = {
  inheritAttrs: false,

  props: {
    value: { default: undefined },
    name: { type: String, default: '' },
  },

  emits: ['update:value'],

  setup(props, { emit }) {
    const selectedType = ref(uiTypeOf(props.value));
    // Set on the emit that follows our own edit, so the watcher below does not
    // re-infer the type (and yank the selector) from a coerced/blank value.
    let internal = false;

    const rawValue = computed(() => rawValueOf(props.value));
    const childComponent = computed(() => EDITORS[selectedType.value] || InputArgText);

    watch(
      () => props.value,
      (value) => {
        if (internal) {
          internal = false;
          return;
        }
        selectedType.value = uiTypeOf(value);
      },
      { immediate: true },
    );

    function emitValue(raw) {
      internal = true;
      emit('update:value', wrap(selectedType.value, raw));
    }

    function onTypeChange(event) {
      selectedType.value = event.target.value;
      emitValue(coerceTo(selectedType.value, rawValue.value));
    }

    function onChildUpdate(raw) {
      emitValue(raw);
    }

    return { selectedType, TYPE_OPTIONS, childComponent, rawValue, onTypeChange, onChildUpdate };
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
    <component :is="childComponent" :value="rawValue" :name="name" @update:value="onChildUpdate" />
  </div>
</div>
`,
};

export default InputArgLiteralValue;
