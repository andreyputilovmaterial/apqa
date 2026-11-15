import { computed, reactive, ref, watch } from 'vue';

import InputSearchSelect from '../../search_select/index';
import { deepClone } from '../shared';

import './styles.css';

function defaultArgValue(arg) {
  if (arg.default !== undefined) return deepClone(arg.default);
  switch (arg.type) {
    case 'boolean':
      return false;
    case 'list':
      return [];
    case 'number':
    case 'path':
      // A blank number/path is not a value — store it as `sysmissing` (null).
      return null;
    case 'cmdlet-chains':
      return [];
    case 'cmdlet-chain':
      return [];
    case 'json':
    case 'literal-value':
      return null;
    default:
      return '';
  }
}

// App-level input for one cmdlet. When nothing is selected it renders a single
// drop down; once a cmdlet is chosen it renders one input per argument (from the
// cmdlet's metadata) plus a clear button that returns to the drop-down state.
// The value is `{ cmdlet, args }`, or `null`/`undefined` when empty, and it
// follows the native input contract (v-model/modelValue + update:modelValue +
// input/change).
//
// `cmdlets` is the *full* metadata list (used to look up the selected cmdlet's
// arg schema and passed through to nested chains). `kinds` (optional) narrows
// the drop down to the given cmdlet kinds. Each argument is rendered by the
// `component-input-cmdlet-arg` editor, which delegates the control to the
// per-type arg editors.
const InputCmdlet = {
  inheritAttrs: false,

  props: {
    modelValue: { type: Object, default: undefined },
    cmdlets: { type: Array, default: () => [] },
    kinds: { type: Array, default: null },
    name: { type: String, default: '' },
    placeholder: { type: String, default: 'Select cmdlet…' },
  },

  emits: ['update:modelValue', 'change', 'input'],

  components: {
    'input-search-select': InputSearchSelect,
  },

  template: `
<div class="apqa-input-cmdlet">
  <input-search-select
    v-if="!selected"
    :model-value="null"
    :options="candidateNames"
    :placeholder="placeholder"
    :name="name"
    @update:model-value="selectCmdlet"
  />

  <div v-else class="apqa-input-cmdlet-selected">
    <span class="apqa-input-cmdlet-name">{{ selected.name }}</span>
    <button type="button" class="apqa-input-cmdlet-toggle-help" :aria-expanded="String(helpOpen)" @click="helpOpen = !helpOpen">{{ helpOpen ? '▴' : '▾' }}</button>
    <button type="button" class="apqa-input-cmdlet-clear" aria-label="Remove cmdlet" @click="clear">×</button>
  </div>

  <div v-if="selected && helpOpen && selected.help" class="apqa-input-cmdlet-help">{{ selected.help }}</div>

  <div v-if="selected && selected.args.length" class="apqa-input-cmdlet-args">
    <component-input-cmdlet-arg
      v-for="arg in selected.args"
      :key="arg.name"
      :arg="arg"
      :value="args[arg.name]"
      :cmdlets="cmdlets"
      :name="arg.name"
      @update:value="setArg(arg, $event)"
    />
  </div>
</div>
`,

  setup(props, { emit }) {
    const args = reactive({});
    const helpOpen = ref(true);

    function findCmdlet(name) {
      if (!name) return null;
      return (props.cmdlets || []).find((c) => c.name === name) || { name, args: [] };
    }

    const selected = computed(() => findCmdlet(props.modelValue?.cmdlet));

    const candidates = computed(() => {
      const list = props.cmdlets || [];
      if (!props.kinds || !props.kinds.length) return list;
      const set = new Set(props.kinds);
      return list.filter((c) => set.has(c.kind));
    });

    const candidateNames = computed(() => candidates.value.map((c) => c.name));

    function resetArgs() {
      for (const key of Object.keys(args)) delete args[key];
      const value = props.modelValue;
      const schema = findCmdlet(value?.cmdlet);
      const base = value?.args || {};
      for (const arg of schema?.args || []) {
        args[arg.name] = arg.name in base ? base[arg.name] : defaultArgValue(arg);
      }
    }

    // Rebuild the local arg state only when the *cmdlet* changes (a new
    // selection or a clear). Arg edits within the same cmdlet do not re-run
    // this, so the user keeps their text and focus.
    watch(() => props.modelValue?.cmdlet ?? null, resetArgs, { immediate: true });

    function emitValue() {
      if (!selected.value) return;
      const out = {};
      for (const arg of selected.value.args || []) out[arg.name] = args[arg.name];
      emit('update:modelValue', { cmdlet: selected.value.name, args: out });
      emit('input', { cmdlet: selected.value.name, args: out });
    }

    function selectCmdlet(name) {
      if (!name) {
        clear();
        return;
      }
      emit('update:modelValue', { cmdlet: name, args: {} });
      emit('change', { cmdlet: name, args: {} });
    }

    function clear() {
      emit('update:modelValue', null);
      emit('change', null);
    }

    function setArg(arg, value) {
      args[arg.name] = value;
      emitValue();
    }

    return {
      args,
      helpOpen,
      selected,
      candidateNames,
      selectCmdlet,
      clear,
      setArg,
    };
  },
};

export default InputCmdlet;
