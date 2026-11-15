import { computed } from 'vue';

import './styles.css';

// `strings` arg editor: a list of strings with add/remove rows (one text input
// per value). An empty list is a real empty `[]`, not `sysmissing`.
const InputArgStrings = {
  inheritAttrs: false,

  props: {
    value: { default: () => [] },
  },

  emits: ['update:value'],

  setup(props, { emit }) {
    const items = computed(() => (Array.isArray(props.value) ? props.value : []));

    function setItem(index, value) {
      const next = items.value.slice();
      next[index] = value;
      emit('update:value', next);
    }

    function addItem() {
      emit('update:value', [...items.value, '']);
    }

    function removeItem(index) {
      const next = items.value.slice();
      next.splice(index, 1);
      emit('update:value', next);
    }

    return { items, setItem, addItem, removeItem };
  },

  template: `
<div class="apqa-input-cmdlet-arg-strings">
  <div v-for="(item, index) in items" :key="index" class="apqa-input-cmdlet-arg-string-item">
    <input
      type="text"
      class="apqa-input-cmdlet-arg-input apqa-input-cmdlet-arg-string-input"
      :value="item"
      @input="setItem(index, $event.target.value)"
    />
    <button type="button" class="apqa-input-cmdlet-arg-string-remove" @click="removeItem(index)">×</button>
  </div>
  <button type="button" class="apqa-input-cmdlet-arg-add-string" @click="addItem">Add value</button>
</div>
`,
};

export default InputArgStrings;
