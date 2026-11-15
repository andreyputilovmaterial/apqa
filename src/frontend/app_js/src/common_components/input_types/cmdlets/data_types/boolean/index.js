// `boolean` arg editor: a plain checkbox. Booleans are strictly two-valued
// (true/false); they have no `sysmissing` state.
const InputArgBoolean = {
  inheritAttrs: false,

  props: {
    value: { default: undefined },
    name: { type: String, default: '' },
  },

  emits: ['update:value'],

  template: `
<span class="apqa-input-cmdlet-arg-bool">
  <input type="checkbox" :name="name" :checked="!!value" @change="$emit('update:value', $event.target.checked)" />
</span>
`,
};

export default InputArgBoolean;
