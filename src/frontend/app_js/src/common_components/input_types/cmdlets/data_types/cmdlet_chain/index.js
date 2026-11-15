// `cmdlet-chain` arg editor: a single nested cmdlet chain (e.g. `map`'s
// `transform` or `where`'s `predicate`). The first slot offers
// processors/terminals because a nested chain receives a piped value.
const InputArgCmdletChain = {
  inheritAttrs: false,

  props: {
    value: { default: () => [] },
    cmdlets: { type: Array, default: () => [] },
  },

  emits: ['update:value'],

  template: `
<div class="apqa-input-cmdlet-arg-chain">
  <component-input-cmdlet-chain :model-value="value" :cmdlets="cmdlets" :first-kinds="['processor', 'terminal']" @update:model-value="$emit('update:value', $event)" />
</div>
`,
};

export default InputArgCmdletChain;
