import Cmdlet from './cmdlet';

const CmdletChain = {
  props: ['chain'],

  components: {
    'cmdlet': Cmdlet,
  },

  template: `
<code class="apqa-cmdlet-chain">
  <template v-if="chain && chain.length">
    <template v-for="(cmdlet, index) in chain" :key="index">
      <span v-if="index > 0" class="apqa-cmdlet-chain-pipe">|</span>
      <cmdlet :cmdlet="cmdlet" />
    </template>
  </template>
  <span v-else class="apqa-cmdlet-chain-empty">(empty)</span>
</code>
`,
};

export default CmdletChain;
