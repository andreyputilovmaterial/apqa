// `number` arg editor: a numeric input. A blank number is not a value — it is
// stored as `sysmissing` (null); non-numeric text is kept as-is.
const InputArgNumber = {
  inheritAttrs: false,

  props: {
    value: { default: undefined },
    name: { type: String, default: '' },
  },

  emits: ['update:value'],

  setup(props, { emit }) {
    function onInput(event) {
      const value = event.target.value;
      if (value === '' || value == null) {
        emit('update:value', null);
        return;
      }
      const number = Number(value);
      emit('update:value', Number.isNaN(number) ? value : number);
    }
    return { onInput };
  },

  template: `<input type="number" class="apqa-input-cmdlet-arg-input" :name="name" :value="value" @input="onInput" />`,
};

export default InputArgNumber;
