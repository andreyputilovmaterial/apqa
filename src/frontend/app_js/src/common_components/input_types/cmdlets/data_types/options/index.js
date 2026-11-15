// `options` arg editor: a single-select drop down built from `arg.options`.
const InputArgOptions = {
  inheritAttrs: false,

  props: {
    value: { default: undefined },
    arg: { type: Object, default: () => ({}) },
    name: { type: String, default: '' },
  },

  emits: ['update:value'],

  template: `
<select class="apqa-input-cmdlet-arg-input" :name="name" :value="value" @change="$emit('update:value', $event.target.value)">
  <option v-for="o in arg.options" :key="o" :value="o">{{ o }}</option>
</select>
`,
};

export default InputArgOptions;
