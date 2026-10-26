import CmdletChain from './cmdlet_chain';

// One folder alias row: `name: chain`, shown inside an expanded folder in the
// QC-rules tree. The chain reuses the same `CmdletChain` renderer as rules.
const AliasRecord = {
  props: ['alias'],

  components: {
    'cmdlet-chain': CmdletChain,
  },

  template: `
<li class="apqa-alias-record">
  <span class="apqa-alias-record-name">{{ alias.name }}</span>
  <span class="apqa-alias-record-colon" aria-hidden="true">:</span>
  <cmdlet-chain :chain="alias.chain" />
</li>
`,
};

export default AliasRecord;
