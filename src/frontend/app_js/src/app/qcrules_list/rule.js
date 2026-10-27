import { computed } from 'vue';

import CmdletChain from './cmdlet_chain';
import Comparison from './comparison';
import ComponentFormatDatetime from '@/common_components/format_datetime/index';
import MarksBadges, { UNFINISHED_MESSAGE } from './marks_badges';
import { isUnfinished, markNamesForRecord } from './grouping';

const Rule = {
  props: ['record'],

  emits: ['toggle'],

  components: {
    'cmdlet-chain': CmdletChain,
    'comparison': Comparison,
    'component-format-datetime': ComponentFormatDatetime,
    'marks-badges': MarksBadges,
  },

  template: `
<div class="apqa-qcrules-entry apqa-qcrules-entry-rule apqa-qcrules-list-item">
  <div
    class="apqa-qcrules-list-item-head"
    role="button"
    tabindex="0"
    @click="$emit('toggle')"
    @keydown.enter.prevent="$emit('toggle')"
  >
    <span class="apqa-qcrules-list-item-name">{{ record.name }}</span>
    <span v-if="record.comment" class="apqa-qcrules-list-item-comment">{{ record.comment }}</span>
    <span v-if="unfinished" class="apqa-rule-unfinished-note">{{ UNFINISHED_MESSAGE }}</span>
  </div>
  <div class="apqa-qcrules-list-item-definition">
    <cmdlet-chain :chain="record.left" />
    <comparison :op="record.op" />
    <cmdlet-chain :chain="record.right" />
  </div>
  <div class="apqa-qcrules-list-item-meta">
    <span v-if="record.tags.length" class="apqa-qcrules-list-item-tags">{{ record.tags.join(', ') }}</span>
    <span v-if="record.created_at" class="apqa-qcrules-list-item-created">created <component-format-datetime :dt="record.created_at" /></span>
  </div>
  <marks-badges :marks="marks" />
</div>
`,

  setup(props) {
    const unfinished = computed(() => isUnfinished(props.record));
    const marks = computed(() => markNamesForRecord(props.record));
    return { UNFINISHED_MESSAGE, unfinished, marks };
  },
};

export default Rule;
