import { ref, watch } from 'vue';

function stringifyJson(value) {
  return value == null ? '' : JSON.stringify(value);
}

// `json` arg editor: a text input holding raw JSON. The raw text is kept
// (unreformatted) while the user types; on every change it is parsed and the
// parsed value is emitted, or `null` (`sysmissing`) for a blank input. Invalid
// JSON is shown as an error and does not change the value. `null` *is*
// `sysmissing` — there is no way to store a JSON `null` value.
const InputArgJson = {
  inheritAttrs: false,

  props: {
    value: { default: undefined },
    name: { type: String, default: '' },
  },

  emits: ['update:value'],

  setup(props, { emit }) {
    const rawText = ref('');
    const error = ref('');
    // Set to true on the emit that follows our own input, so the watcher below
    // does not reformat the user's raw text back from the parsed value.
    let internal = false;

    watch(
      () => props.value,
      (value) => {
        if (internal) {
          internal = false;
          return;
        }
        rawText.value = stringifyJson(value);
        error.value = '';
      },
      { immediate: true },
    );

    function onInput(event) {
      const text = event.target.value;
      rawText.value = text;
      error.value = '';
      if (text == null || text.trim() === '') {
        internal = true;
        emit('update:value', null);
        return;
      }
      try {
        internal = true;
        emit('update:value', JSON.parse(text));
      } catch {
        error.value = 'Invalid JSON';
      }
    }

    return { rawText, error, onInput };
  },

  template: `
<input type="text" class="apqa-input-cmdlet-arg-input" :name="name" :value="rawText" @input="onInput" />
<span v-if="error" class="apqa-input-cmdlet-arg-error">{{ error }}</span>
`,
};

export default InputArgJson;
