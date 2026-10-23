// One global alias (definition) row: `NAME = value`, plus an optional grey
// comment. Rendered as an `<li>` inside the aliases list.
const DefinitionRecord = {
  props: ['record'],

  template: `
<li class="apqa-definition-record" :class="record._filterMeta.cssClasses">
  <span class="apqa-definition-record-name">{{ record.name }}</span>
  <span class="apqa-definition-record-eq" aria-hidden="true">=</span>
  <code class="apqa-definition-record-value">{{ record.value }}</code>
  <span v-if="record.comment" class="apqa-definition-record-comment">{{ record.comment }}</span>
</li>
`,
};

export default DefinitionRecord;