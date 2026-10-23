import CmdletChain from './cmdlet_chain';
import Comparison from './comparison';
import ComponentFormatDatetime from '../../common_components/format_datetime/index';

const Rule = {
  props: ['record'],

  components: {
    'cmdlet-chain': CmdletChain,
    'comparison': Comparison,
    'component-format-datetime': ComponentFormatDatetime,
  },

  template: `
<li class="apqa-qcrules-list-item" :class="record._filterMeta.cssClasses">
  <div class="apqa-qcrules-list-item-head">
    <span class="apqa-qcrules-list-item-name">{{ record.name }}</span>
  </div>
  <div v-if="record.comment" class="apqa-qcrules-list-item-comment">{{ record.comment }}</div>
  <div class="apqa-qcrules-list-item-definition">
    <cmdlet-chain :chain="record.left" />
    <comparison :op="record.op" />
    <cmdlet-chain :chain="record.right" />
  </div>
  <div v-if="record.markers.length" class="apqa-qcrules-list-item-markers">
    <span v-for="marker in record.markers" :key="marker" class="apqa-qcrules-list-item-marker">{{ marker }}</span>
  </div>
  <div class="apqa-qcrules-list-item-meta">
    <span v-if="record.tags.length" class="apqa-qcrules-list-item-tags">{{ record.tags.join(', ') }}</span>
    <span v-if="record.created_at" class="apqa-qcrules-list-item-created">created <component-format-datetime :dt="record.created_at" /></span>
  </div>
</li>
`,
};

export default Rule;
