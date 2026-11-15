// `text` arg editor: a plain text input; the value stays a string (an empty
// string is a valid text value, never `sysmissing`).
const InputArgText = {
  inheritAttrs: false,

  props: {
    value: { default: undefined },
    name: { type: String, default: '' },
  },

  emits: ['update:value'],

  template: `<input type="text" class="apqa-input-cmdlet-arg-input" :name="name" :value="value" @input="$emit('update:value', $event.target.value)" />`,
};

export default InputArgText;
