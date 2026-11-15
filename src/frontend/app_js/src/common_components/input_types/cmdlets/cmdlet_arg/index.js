import { computed } from 'vue';

import './styles.css';

// App-level editor for one cmdlet argument (parameter). It renders the label
// plus the per-type control, delegating the control to the
// `component-input-cmdlet-arg-<type>` editor via a dynamic component (so the
// type-specific editors are referenced by their global tags).
//
// It is intentionally "dumb": the parent (cmdlet editor / comparison-op editor)
// owns the args state, passes the current `value` in, and receives the typed
// value back through `update:value`.
const InputCmdletArg = {
  inheritAttrs: false,

  props: {
    arg: { type: Object, required: true },
    value: { default: undefined },
    cmdlets: { type: Array, default: () => [] },
    name: { type: String, default: '' },
  },

  emits: ['update:value'],

  setup(props) {
    const inputComponent = computed(() =>
      `component-input-cmdlet-arg-${props.arg.type || 'text'}`,
    );
    return { inputComponent };
  },

  template: `
<label class="apqa-input-cmdlet-arg" :class="'apqa-input-cmdlet-arg-' + (arg.type || 'text')">
  <span class="apqa-input-cmdlet-arg-label">{{ arg.name }}<span v-if="arg.required" class="apqa-input-cmdlet-arg-required">*</span></span>
  <component :is="inputComponent" :value="value" :arg="arg" :cmdlets="cmdlets" :name="arg.name" @update:value="$emit('update:value', $event)" />
  <span v-if="arg.description" class="apqa-input-cmdlet-arg-help">{{ arg.description }}</span>
</label>
`,
};

export default InputCmdletArg;
