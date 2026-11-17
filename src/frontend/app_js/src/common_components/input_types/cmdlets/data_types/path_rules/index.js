import { computed } from 'vue';

import './styles.css';

const RULE_TYPES = ['eq', 'startswith', 'endswith', 'contains', 'regex'];

function emptyRule() {
  return { name: '', type: 'eq', pattern: '', case_insensitive: false };
}

// `path-rules` arg editor: a list of structured exclude rules with add/remove
// rows. Each row edits one rule's display name, match type, pattern, and
// case-insensitive flag. An empty list is a real empty `[]`, not `sysmissing`.
const InputArgPathRules = {
  inheritAttrs: false,

  props: {
    value: { default: () => [] },
  },

  emits: ['update:value'],

  setup(props, { emit }) {
    const items = computed(() => {
      const list = Array.isArray(props.value) ? props.value : [];
      return list.map((rule) => {
        const r = rule && typeof rule === 'object' ? rule : {};
        return {
          name: r.name ?? '',
          type: RULE_TYPES.includes(r.type) ? r.type : 'eq',
          pattern: r.pattern ?? '',
          case_insensitive: Boolean(r.case_insensitive),
        };
      });
    });

    function setItem(index, field, value) {
      const next = items.value.map((rule, i) =>
        i === index ? { ...rule, [field]: value } : rule,
      );
      emit('update:value', next);
    }

    function addRule() {
      emit('update:value', [...items.value, emptyRule()]);
    }

    function removeRule(index) {
      const next = items.value.slice();
      next.splice(index, 1);
      emit('update:value', next);
    }

    return { items, RULE_TYPES, setItem, addRule, removeRule };
  },

  template: `
<div class="apqa-input-cmdlet-arg-path-rules">
  <div v-for="(rule, index) in items" :key="index" class="apqa-input-cmdlet-arg-path-rule">
    <input
      type="text"
      class="apqa-input-cmdlet-arg-input apqa-input-cmdlet-arg-rule-name"
      placeholder="name"
      :value="rule.name"
      @input="setItem(index, 'name', $event.target.value)"
    />
    <select
      class="apqa-input-cmdlet-arg-input"
      :value="rule.type"
      @change="setItem(index, 'type', $event.target.value)"
    >
      <option v-for="t in RULE_TYPES" :key="t" :value="t">{{ t }}</option>
    </select>
    <input
      type="text"
      class="apqa-input-cmdlet-arg-input apqa-input-cmdlet-arg-rule-pattern"
      placeholder="pattern"
      :value="rule.pattern"
      @input="setItem(index, 'pattern', $event.target.value)"
    />
    <label class="apqa-input-cmdlet-arg-rule-ci" title="case-insensitive">
      <input type="checkbox" :checked="rule.case_insensitive" @change="setItem(index, 'case_insensitive', $event.target.checked)" />
      <span>ci</span>
    </label>
    <button type="button" class="apqa-input-cmdlet-arg-string-remove" @click="removeRule(index)">×</button>
  </div>
  <button type="button" class="apqa-input-cmdlet-arg-add-string" @click="addRule">Add rule</button>
</div>
`,
};

export default InputArgPathRules;
