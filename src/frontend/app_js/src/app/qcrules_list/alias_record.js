// One folder alias row: `name: chain`, shown inside an expanded folder in the
// QC-rules tree. The chain reuses the same display `cmdlet-chain` renderer as
// rules.
const AliasRecord = {
  props: ['alias'],

  template: `
<li class="apqa-alias-record">
  <span class="apqa-alias-record-name">{{ alias.name }}</span>
  <span class="apqa-alias-record-colon" aria-hidden="true">:</span>
  <component-cmdlet-chain-compact :chain="alias.chain" />
</li>
`,
};

export default AliasRecord;
