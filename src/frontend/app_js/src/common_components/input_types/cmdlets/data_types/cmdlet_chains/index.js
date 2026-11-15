import { computed } from 'vue';

import './styles.css';

// `cmdlet-chains` arg editor: a list of nested cmdlet chains (e.g. `and`/`or`/
// `bit-*` `operands`), with add/remove controls.
const InputArgCmdletChains = {
  inheritAttrs: false,

  props: {
    value: { default: () => [] },
    cmdlets: { type: Array, default: () => [] },
  },

  emits: ['update:value'],

  setup(props, { emit }) {
    const chains = computed(() => (Array.isArray(props.value) ? props.value : []));

    function addChain() {
      emit('update:value', [...chains.value, []]);
    }

    function removeChain(index) {
      const next = chains.value.slice();
      next.splice(index, 1);
      emit('update:value', next);
    }

    function setChain(index, value) {
      const next = chains.value.slice();
      next[index] = value;
      emit('update:value', next);
    }

    return { chains, addChain, removeChain, setChain };
  },

  template: `
<div class="apqa-input-cmdlet-arg-chains">
  <div v-for="(chain, ci) in chains" :key="ci" class="apqa-input-cmdlet-chain-item">
    <component-input-cmdlet-chain :model-value="chains[ci]" :cmdlets="cmdlets" @update:model-value="setChain(ci, $event)" />
    <button type="button" class="apqa-input-cmdlet-chain-item-remove" @click="removeChain(ci)">×</button>
  </div>
  <button type="button" class="apqa-input-cmdlet-add-chain" @click="addChain">Add chain</button>
</div>
`,
};

export default InputArgCmdletChains;
