import { computed, reactive, ref, watch } from 'vue';

import InputSearchSelect from '../input_search_select/index';

import './styles.css';

function deepClone(value) {
  return JSON.parse(JSON.stringify(value));
}

function defaultArgValue(arg) {
  if (arg.default !== undefined) return deepClone(arg.default);
  switch (arg.type) {
    case 'boolean':
      return false;
    case 'list':
      return [];
    case 'cmdlet-chains':
      return [];
    case 'json':
      return null;
    default:
      return '';
  }
}

function stringifyJson(value) {
  return value == null ? '' : JSON.stringify(value);
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
// the drop down to the given cmdlet kinds.
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
    <label v-for="arg in selected.args" :key="arg.name" class="apqa-input-cmdlet-arg" :class="'apqa-input-cmdlet-arg-' + arg.type">
      <span class="apqa-input-cmdlet-arg-label">{{ arg.name }}<span v-if="arg.required" class="apqa-input-cmdlet-arg-required">*</span></span>

      <input v-if="arg.type === 'json'" type="text" class="apqa-input-cmdlet-arg-input" :name="arg.name" :value="rawJson[arg.name]" @input="setJson(arg, $event.target.value)" />
      <span v-else-if="arg.type === 'boolean'" class="apqa-input-cmdlet-arg-bool">
        <input type="checkbox" :name="arg.name" :checked="!!args[arg.name]" @change="setArg(arg, $event.target.checked)" />
      </span>
      <select v-else-if="arg.type === 'options'" class="apqa-input-cmdlet-arg-input" :name="arg.name" :value="args[arg.name]" @change="setArg(arg, $event.target.value)">
        <option v-for="o in arg.options" :key="o" :value="o">{{ o }}</option>
      </select>
      <input v-else-if="arg.type === 'list'" type="text" class="apqa-input-cmdlet-arg-input" :name="arg.name" :value="listText(arg)" @input="setList(arg, $event.target.value)" />
      <div v-else-if="arg.type === 'cmdlet-chains'" class="apqa-input-cmdlet-arg-chains">
        <div v-for="(chain, ci) in chainsValue(arg)" :key="ci" class="apqa-input-cmdlet-chain-item">
          <component-input-cmdlet-chain :model-value="chainsValue(arg)[ci]" :cmdlets="cmdlets" @update:model-value="setChain(arg, ci, $event)" />
          <button type="button" class="apqa-input-cmdlet-chain-item-remove" @click="removeChain(arg, ci)">×</button>
        </div>
        <button type="button" class="apqa-input-cmdlet-add-chain" @click="addChain(arg)">Add chain</button>
      </div>
      <input v-else :type="inputType(arg)" class="apqa-input-cmdlet-arg-input" :name="arg.name" :value="args[arg.name]" @input="setArg(arg, $event.target.value)" />

      <span v-if="arg.description" class="apqa-input-cmdlet-arg-help">{{ arg.description }}</span>
      <span v-if="jsonError[arg.name]" class="apqa-input-cmdlet-arg-error">{{ jsonError[arg.name] }}</span>
    </label>
  </div>
</div>
`,

  setup(props, { emit }) {
    const args = reactive({});
    const rawJson = reactive({});
    const jsonError = reactive({});
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
      for (const key of Object.keys(rawJson)) delete rawJson[key];
      for (const key of Object.keys(jsonError)) delete jsonError[key];

      const value = props.modelValue;
      const schema = findCmdlet(value?.cmdlet);
      const base = value?.args || {};
      for (const arg of schema?.args || []) {
        args[arg.name] = arg.name in base ? base[arg.name] : defaultArgValue(arg);
        if (arg.type === 'json') rawJson[arg.name] = stringifyJson(args[arg.name]);
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

    function setJson(arg, text) {
      rawJson[arg.name] = text;
      jsonError[arg.name] = '';
      if (text == null || text.trim() === '') {
        args[arg.name] = null;
        emitValue();
        return;
      }
      try {
        args[arg.name] = JSON.parse(text);
        emitValue();
      } catch (e) {
        jsonError[arg.name] = 'Invalid JSON';
      }
    }

    function setList(arg, text) {
      args[arg.name] = String(text)
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s !== '');
      emitValue();
    }

    function listText(arg) {
      return (Array.isArray(args[arg.name]) ? args[arg.name] : []).join(', ');
    }

    function chainsValue(arg) {
      return Array.isArray(args[arg.name]) ? args[arg.name] : [];
    }

    function addChain(arg) {
      if (!Array.isArray(args[arg.name])) args[arg.name] = [];
      args[arg.name].push([]);
      emitValue();
    }

    function removeChain(arg, index) {
      if (!Array.isArray(args[arg.name])) return;
      args[arg.name].splice(index, 1);
      emitValue();
    }

    function setChain(arg, index, value) {
      if (!Array.isArray(args[arg.name])) args[arg.name] = [];
      args[arg.name][index] = value;
      emitValue();
    }

    function inputType(arg) {
      return arg.type === 'number' ? 'number' : 'text';
    }

    return {
      args,
      rawJson,
      jsonError,
      helpOpen,
      selected,
      candidates,
      candidateNames,
      selectCmdlet,
      clear,
      setArg,
      setJson,
      setList,
      listText,
      chainsValue,
      addChain,
      removeChain,
      setChain,
      inputType,
    };
  },
};

export default InputCmdlet;
