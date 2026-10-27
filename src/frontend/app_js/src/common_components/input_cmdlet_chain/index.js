import { computed } from 'vue';

import InputCmdlet from '../input_cmdlet/index';

import './styles.css';

// App-level input for a chain of cmdlets. Renders a dotted-border "drop area"
// listing the selected cmdlets, plus one trailing placeholder drop down for the
// next cmdlet whenever the last selected one is filled. The value is an array of
// `{ cmdlet, args }` (empty array when nothing is selected) and it follows the
// native input contract.
//
// The first slot only offers `kind: 'source'` cmdlets (they need no piped input);
// later slots offer processors/terminals.
const InputCmdletChain = {
  inheritAttrs: false,

  props: {
    modelValue: { type: Array, default: () => [] },
    cmdlets: { type: Array, default: () => [] },
  },

  emits: ['update:modelValue', 'change', 'input'],

  components: {
    'input-cmdlet': InputCmdlet,
  },

  template: `
<div class="apqa-input-cmdlet-chain">
  <div v-for="(entry, index) in entries" :key="index" class="apqa-input-cmdlet-chain-slot">
    <input-cmdlet
      :model-value="entry"
      :cmdlets="cmdlets"
      :kinds="kindsFor(index)"
      @update:model-value="onUpdateAt(index, $event)"
    />
  </div>

  <div class="apqa-input-cmdlet-chain-slot apqa-input-cmdlet-chain-slot-next">
    <input-cmdlet
      :model-value="null"
      :cmdlets="cmdlets"
      :kinds="kindsFor(entries.length)"
      :placeholder="entries.length === 0 ? 'Select source…' : 'Select next cmdlet…'"
      @update:model-value="onAppend($event)"
    />
  </div>
</div>
`,

  setup(props, { emit }) {
    const entries = computed(() => (props.modelValue || []).filter((c) => c != null));

    function kindsFor(index) {
      return index === 0 ? ['source'] : ['processor', 'terminal'];
    }

    function normalizeChain() {
      return (props.modelValue || []).filter((c) => c != null);
    }

    function emitChain(next) {
      emit('update:modelValue', next);
      emit('change', next);
      emit('input', next);
    }

    function onUpdateAt(index, value) {
      const next = normalizeChain();
      if (value == null) next.splice(index, 1);
      else next[index] = value;
      emitChain(next);
    }

    function onAppend(value) {
      if (value == null) return;
      const next = normalizeChain();
      next.push(value);
      emitChain(next);
    }

    return { entries, kindsFor, onUpdateAt, onAppend };
  },
};

export default InputCmdletChain;
