import { computed, reactive, watch } from 'vue';

import { deepClone } from '../shared';

import './styles.css';

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
//
// Each `op_args` entry is rendered by the shared `component-input-cmdlet-arg`
// editor (op_args use the same arg-schema shape as cmdlet args).
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
    <component-input-cmdlet-arg
      v-for="arg in selected.op_args"
      :key="arg.name"
      :arg="arg"
      :value="args[arg.name]"
      :name="arg.name"
      @update:value="setArg(arg, $event)"
    />
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
      args[arg.name] = value;
      emitValue();
    }

    return { args, selected, selectOp, clear, setArg };
  },
};

export default InputComparisonOp;
