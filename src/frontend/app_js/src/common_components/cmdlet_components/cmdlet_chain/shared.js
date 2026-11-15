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
    <template v-for="(cmdlet, index) in chain" :key="index">
      <span v-if="index > 0" class="apqa-cmdlet-chain-pipe">|</span>
      <component :is="cmdletComponent" :cmdlet="cmdlet" :cmdlets="cmdlets" />
    </template>
  </template>
  <span v-else class="apqa-cmdlet-chain-empty">(empty)</span>
</code>
`,
  };
}
