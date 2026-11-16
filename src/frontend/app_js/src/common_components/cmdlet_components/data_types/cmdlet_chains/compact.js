import { computed } from 'vue';

// `cmdlet-chains` arg value (a list of nested chains) — compact display.
// Each nested chain is rendered with the same compact chain chip used by the
// rule list, separated by a comma, so a logical/bitwise operand list reads
// `AND( chain1, chain2, chain3 )` when the cmdlet's compact spec supplies the
// surrounding keyword and parentheses.
export default {
  props: {
    value: { default: () => [] },
    cmdlets: { type: Array, default: () => [] },
  },

  setup(props) {
    const chains = computed(() => (Array.isArray(props.value) ? props.value : []));
    return { chains };
  },

  template: `
<span class="apqa-cmdlet-chains">
  <template v-for="(chain, index) in chains" :key="index">
    <span v-if="index > 0" class="apqa-cmdlet-chains-sep">, </span>
    <component-cmdlet-chain-compact :chain="chain" :cmdlets="cmdlets" />
  </template>
</span>
`,
};
