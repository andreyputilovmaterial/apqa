import CmdletChain from './cmdlet_chain';
import Comparison from './comparison';
import ComponentFormatDatetime from '../../common_components/format_datetime/index';

const Rule = {
  props: ['record'],

  emits: ['toggle'],

  components: {
    'cmdlet-chain': CmdletChain,
    'comparison': Comparison,
    'component-format-datetime': ComponentFormatDatetime,
  },

  template: `
<div class="apqa-qcrules-list-item">
  <div
    class="apqa-qcrules-list-item-head"
    role="button"
    tabindex="0"
    @click="$emit('toggle')"
    @keydown.enter.prevent="$emit('toggle')"
  >
    <span class="apqa-qcrules-list-item-name">{{ record.name }}</span>
    <span v-if="record.comment" class="apqa-qcrules-list-item-comment">{{ record.comment }}</span>
  </div>
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
</div>
`,
};

export default Rule;
