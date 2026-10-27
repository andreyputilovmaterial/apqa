import { computed, reactive, watch } from 'vue';

import './styles.css';

function deepClone(value) {
  return JSON.parse(JSON.stringify(value));
}

function defaultOpArgValue(arg) {
  if (arg.default !== undefined) return deepClone(arg.default);
  if (arg.type === 'boolean') return false;
  if (arg.type === 'json') return null;
  return '';
}

// App-level input for the comparison **op** (the middle part of a rule, from
// the same cmdlet/chain world as the left/right sides): an op selector plus one
// input per op-specific option (`op_args`). The value is `{ op, op_args }`, or
// `null`/`undefined` when empty, following the native input contract. `ops` is
// the comparison-op metadata list from `/functionality/cmdlet-metadata`.
const InputComparisonOp = {
  inheritAttrs: false,

  props: {
    modelValue: { type: Object, default: undefined },
    ops: { type: Array, default: () => [] },
    name: { type: String, default: '' },
    placeholder: { type: String, default: 'Select comparison…' },
  },

  emits: ['update:modelValue', 'change', 'input'],

  template: `
<div class="apqa-input-comparison-op">
  <select v-if="!selected" class="apqa-input-comparison-op-select" :name="name" :value="''" @change="selectOp($event.target.value)">
    <option value="" selected disabled>{{ placeholder }}</option>
    <option v-for="op in ops" :key="op.name" :value="op.name">{{ op.name }}</option>
  </select>

  <div v-else class="apqa-input-comparison-op-selected">
    <span class="apqa-input-comparison-op-name">{{ selected.name }}</span>
    <button type="button" class="apqa-input-comparison-op-clear" aria-label="Remove comparison" @click="clear">×</button>
  </div>

  <div v-if="selected && selected.op_args.length" class="apqa-input-comparison-op-args">
    <label v-for="arg in selected.op_args" :key="arg.name" class="apqa-input-comparison-op-arg">
      <span class="apqa-input-comparison-op-arg-label">{{ arg.name }}</span>

      <span v-if="arg.type === 'boolean'" class="apqa-input-comparison-op-arg-bool">
        <input type="checkbox" :name="arg.name" :checked="!!args[arg.name]" @change="setArg(arg, $event.target.checked)" />
      </span>
      <select v-else-if="arg.type === 'options'" class="apqa-input-comparison-op-arg-input" :name="arg.name" :value="args[arg.name]" @change="setArg(arg, $event.target.value)">
        <option v-for="o in arg.options" :key="o" :value="o">{{ o }}</option>
      </select>
      <input v-else :type="inputType(arg)" class="apqa-input-comparison-op-arg-input" :name="arg.name" :value="args[arg.name]" @input="setArg(arg, $event.target.value)" />

      <span v-if="arg.description" class="apqa-input-comparison-op-arg-help">{{ arg.description }}</span>
    </label>
  </div>
</div>
`,

  setup(props, { emit }) {
    const args = reactive({});

    function findOp(name) {
      if (!name) return null;
      return (props.ops || []).find((op) => op.name === name) || { name, op_args: [] };
    }

    const selected = computed(() => findOp(props.modelValue?.op));

    function resetArgs() {
      for (const key of Object.keys(args)) delete args[key];
      const value = props.modelValue;
      const schema = findOp(value?.op);
      const base = value?.op_args || {};
      for (const arg of schema?.op_args || []) {
        args[arg.name] = arg.name in base ? base[arg.name] : defaultOpArgValue(arg);
      }
    }

    watch(() => props.modelValue?.op ?? null, resetArgs, { immediate: true });

    function emitValue() {
      if (!selected.value) return;
      const out = {};
      for (const arg of selected.value.op_args || []) out[arg.name] = args[arg.name];
      emit('update:modelValue', { op: selected.value.name, op_args: out });
      emit('input', { op: selected.value.name, op_args: out });
    }

    function selectOp(name) {
      if (!name) {
        clear();
        return;
      }
      emit('update:modelValue', { op: name, op_args: {} });
      emit('change', { op: name, op_args: {} });
    }

    function clear() {
      emit('update:modelValue', null);
      emit('change', null);
    }

    function setArg(arg, value) {
      if (arg.type === 'number') {
        if (value === '' || value == null) args[arg.name] = null;
        else {
          const number = Number(value);
          args[arg.name] = Number.isNaN(number) ? value : number;
        }
      } else if (arg.type === 'boolean') {
        args[arg.name] = !!value;
      } else {
        args[arg.name] = value;
      }
      emitValue();
    }

    function inputType(arg) {
      return arg.type === 'number' ? 'number' : 'text';
    }

    return { args, selected, selectOp, clear, setArg, inputType };
  },
};

export default InputComparisonOp;
