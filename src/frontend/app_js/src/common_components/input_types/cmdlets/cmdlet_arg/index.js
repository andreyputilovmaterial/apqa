import { computed, ref, watch } from 'vue';

import './styles.css';

// App-level editor for one cmdlet argument (parameter). It renders the label,
// the per-type control (delegated to the `component-input-cmdlet-arg-<type>`
// editor), and a shared "unset" opt-out that stores `sysmissing` (null) for
// *any* type — the one uniform way to un-set a value across every data type.
//
// Layout: label, control and the "unset" toggle share one vertically-centered
// row; the optional help text sits on its own line below. It is intentionally
// "dumb": the parent (cmdlet editor / comparison-op editor) owns the args state,
// passes the current `value` in, and receives the typed value back through
// `update:value`.
const InputCmdletArg = {
  inheritAttrs: false,

  props: {
    arg: { type: Object, required: true },
    value: { default: undefined },
    cmdlets: { type: Array, default: () => [] },
    name: { type: String, default: '' },
  },

  emits: ['update:value'],

  setup(props, { emit }) {
    const inputComponent = computed(() =>
      `component-input-cmdlet-arg-${props.arg.type || 'text'}`,
    );
    const isUnset = computed(() => props.value === null || props.value === undefined);
    // The last non-sysmissing value, so un-checking "unset" restores it instead
    // of resetting to a default.
    const lastValue = ref(null);
    watch(
      () => props.value,
      (value) => {
        if (value !== null && value !== undefined) lastValue.value = value;
      },
      { immediate: true },
    );

    function defaultForType(type) {
      switch (type) {
        case 'boolean':
          return false;
        case 'list':
        case 'strings':
        case 'path-rules':
        case 'cmdlet-chains':
          return [];
        case 'number':
        case 'path':
        case 'json':
        case 'literal-value':
        case 'cmdlet-chain':
          return null;
        default:
          return '';
      }
    }

    function onToggleUnset(event) {
      if (event.target.checked) {
        emit('update:value', null);
      } else if (lastValue.value !== null && lastValue.value !== undefined) {
        emit('update:value', lastValue.value);
      } else {
        emit('update:value', defaultForType(props.arg.type));
      }
    }

    return { inputComponent, isUnset, onToggleUnset };
  },

  template: `
<div class="apqa-input-cmdlet-arg" :class="'apqa-input-cmdlet-arg-' + (arg.type || 'text')">
  <div class="apqa-input-cmdlet-arg-row">
    <span class="apqa-input-cmdlet-arg-label">{{ arg.name }}<span v-if="arg.required" class="apqa-input-cmdlet-arg-required">*</span></span>
    <div class="apqa-input-cmdlet-arg-control" :class="{ 'is-unset': isUnset }">
      <component :is="inputComponent" :value="value" :arg="arg" :cmdlets="cmdlets" :name="arg.name" @update:value="$emit('update:value', $event)" />
    </div>
    <label class="apqa-input-cmdlet-arg-unset" :title="'unset ' + arg.name + ' (sysmissing)'">
      <input type="checkbox" :checked="isUnset" @change="onToggleUnset" />
      <span>unset</span>
    </label>
  </div>
  <span v-if="arg.description" class="apqa-input-cmdlet-arg-help">{{ arg.description }}</span>
</div>
`,
};

export default InputCmdletArg;
