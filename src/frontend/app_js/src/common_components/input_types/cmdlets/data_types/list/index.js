import { computed } from 'vue';

// `list` arg editor: a text input of comma-separated values, stored as an array
// (an empty input is a real empty list `[]`, not `sysmissing`).
const InputArgList = {
  inheritAttrs: false,

  props: {
    value: { default: () => [] },
    name: { type: String, default: '' },
  },

  emits: ['update:value'],

  setup(props, { emit }) {
    const listText = computed(() => (Array.isArray(props.value) ? props.value : []).join(', '));

    function onInput(event) {
      emit(
        'update:value',
        String(event.target.value)
          .split(',')
          .map((s) => s.trim())
          .filter((s) => s !== ''),
      );
    }

    return { listText, onInput };
  },

  template: `<input type="text" class="apqa-input-cmdlet-arg-input" :name="name" :value="listText" @input="onInput" />`,
};

export default InputArgList;
