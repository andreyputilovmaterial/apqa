import './styles.css';

export function makeCmdletChain(form) {
  const cmdletComponent = `component-cmdlet-${form}`;

  return {
    props: {
      chain: { type: Array, default: () => [] },
      cmdlets: { type: Array, default: () => [] },
    },

    setup() {
      return { cmdletComponent };
    },

    template: `
<code class="apqa-cmdlet-chain">
  <template v-if="chain && chain.length">
    <component
      v-for="(cmdlet, index) in chain"
      :key="index"
      :is="cmdletComponent"
      :cmdlet="cmdlet"
      :cmdlets="cmdlets"
    />
  </template>
  <span v-else class="apqa-cmdlet-chain-empty">(empty)</span>
</code>
`,
  };
}
