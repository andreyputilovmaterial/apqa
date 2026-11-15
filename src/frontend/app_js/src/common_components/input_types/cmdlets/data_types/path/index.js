// `path` arg editor: a plain text input. An empty path is not a value — it is
// stored as `sysmissing` (null).
const InputArgPath = {
  inheritAttrs: false,

  props: {
    value: { default: undefined },
    name: { type: String, default: '' },
  },

  emits: ['update:value'],

  setup(props, { emit }) {
    function onInput(event) {
      const value = event.target.value;
      emit('update:value', value === '' || value == null ? null : value);
    }
    return { onInput };
  },

  template: `<input type="text" class="apqa-input-cmdlet-arg-input" :name="name" :value="value" @input="onInput" />`,
};

export default InputArgPath;
