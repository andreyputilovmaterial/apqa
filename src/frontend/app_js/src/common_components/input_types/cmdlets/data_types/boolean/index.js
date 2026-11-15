// `boolean` arg editor: a `true`/`false` drop down. The value stays a strict
// boolean; `sysmissing` is expressed through the shared "unset" control on the
// surrounding arg editor, never as a third drop-down option.
const InputArgBoolean = {
  inheritAttrs: false,

  props: {
    value: { default: false },
    name: { type: String, default: '' },
  },

  emits: ['update:value'],

  template: `
<select
  class="apqa-input-cmdlet-arg-input"
  :name="name"
  :value="String(value)"
  @change="$emit('update:value', $event.target.value === 'true')"
>
  <option value="false">false</option>
  <option value="true">true</option>
</select>
`,
};

export default InputArgBoolean;
