import { computed, ref } from 'vue';

import './styles.css';

// App-level "tags" input, blog-post style: a list of committed tag chips plus a
// single text box. Typing shows suggestions (from previously used tags) via a
// native <datalist>; Enter or comma commits a new tag. The value is an array of
// strings and it follows the native input contract.
const InputQcruleTags = {
  inheritAttrs: false,

  props: {
    modelValue: { type: Array, default: () => [] },
    suggestions: { type: Array, default: () => [] },
    name: { type: String, default: '' },
    placeholder: { type: String, default: 'Add tag…' },
  },

  emits: ['update:modelValue', 'change', 'input'],

  template: `
<div class="apqa-input-qcrule-tags">
  <ul v-if="tags.length" class="apqa-input-qcrule-tags-list">
    <li v-for="(tag, index) in tags" :key="tag" class="apqa-input-qcrule-tags-item">
      <span class="apqa-input-qcrule-tags-item-label">{{ tag }}</span>
      <button type="button" class="apqa-input-qcrule-tags-remove" aria-label="Remove tag" @click="remove(index)">×</button>
    </li>
  </ul>
  <input
    type="text"
    class="apqa-input-qcrule-tags-input"
    :name="name"
    :placeholder="placeholder"
    :list="listId"
    :value="draft"
    @input="draft = $event.target.value"
    @keydown="onKeydown"
    @blur="commit"
  />
  <datalist :id="listId">
    <option v-for="s in remainingSuggestions" :key="s" :value="s"></option>
  </datalist>
</div>
`,

  setup(props, { emit }) {
    const draft = ref('');
    const listId = `apqa-tags-${Math.random().toString(36).slice(2)}`;

    const tags = computed(() =>
      (props.modelValue || []).filter((t) => t != null && String(t).trim() !== ''),
    );

    const remainingSuggestions = computed(() => {
      const chosen = new Set(tags.value.map(String));
      return (props.suggestions || []).filter((s) => !chosen.has(String(s)));
    });

    function emitTags(next) {
      emit('update:modelValue', next);
      emit('change', next);
      emit('input', next);
    }

    function commit() {
      const value = draft.value.trim();
      if (!value) return;
      const next = tags.value.slice();
      if (!next.includes(value)) next.push(value);
      emitTags(next);
      draft.value = '';
    }

    function onKeydown(event) {
      if (event.key === 'Enter' || event.key === ',') {
        event.preventDefault();
        commit();
      } else if (event.key === 'Backspace' && draft.value === '') {
        const next = tags.value.slice();
        if (next.length) {
          next.pop();
          emitTags(next);
        }
      }
    }

    function remove(index) {
      const next = tags.value.slice();
      next.splice(index, 1);
      emitTags(next);
    }

    return { draft, listId, tags, remainingSuggestions, commit, onKeydown, remove };
  },
};

export default InputQcruleTags;
