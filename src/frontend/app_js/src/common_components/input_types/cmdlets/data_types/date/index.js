// `date` arg editor — placeholder. No backend arg type `date` exists yet, so
// this editor is dormant until one is registered; for now it is a plain text
// input like `text`.
const InputArgDate = {
  inheritAttrs: false,

  props: {
    value: { default: undefined },
    name: { type: String, default: '' },
  },

  emits: ['update:value'],

  template: `<input type="text" class="apqa-input-cmdlet-arg-input" :name="name" :value="value" @input="$emit('update:value', $event.target.value)" />`,
};

export default InputArgDate;
