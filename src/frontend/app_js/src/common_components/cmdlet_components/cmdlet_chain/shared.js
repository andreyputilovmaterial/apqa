import './styles.css';

export function makeCmdletChain(form) {
  const cmdletComponent = `component-cmdlet-${form}`;

  return {
    props: {
      chain: { type: Array, default: () => [] },
      cmdlets: { type: Array, default: () => [] },
    },

    setup() {
      // A real tab character, rendered as a hidden separator between adjacent
      // chips (see `.apqa-cmdlet-separator`), so copy-as-text separates the
      // chips with tabs while the visible layout stays unchanged.
      return { cmdletComponent, tabChar: '\t' };
    },

    template: `
<code class="apqa-cmdlet-chain">
  <template v-if="chain && chain.length">
    <template v-for="(cmdlet, index) in chain" :key="index">
      <span v-if="index > 0" class="apqa-cmdlet-separator" aria-hidden="true">{{ tabChar }}</span>
      <component
        :is="cmdletComponent"
        :cmdlet="cmdlet"
        :cmdlets="cmdlets"
      />
    </template>
  </template>
  <span v-else class="apqa-cmdlet-chain-empty">(empty)</span>
</code>
`,
  };
}
