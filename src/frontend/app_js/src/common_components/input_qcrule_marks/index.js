import InputMultipunch from '../input_multipunch/index';

import './styles.css';

// The globally supported QC-rule markers (pytest modifiers). This is the single
// place to extend the list — e.g. future conditional platform markers driven by
// environment variables (see docs/development.md "Markers").
export const MARKERS = ['skip', 'xfail'];

// App-level input for a rule's markers. A thin proxy over the multi-punch drop
// down: the *single* place that owns which markers exist, so the representation
// can change (multi-punch, checkboxes, …) without touching the rule form. The
// value is an array of marker names.
const InputQcruleMarks = {
  inheritAttrs: false,

  props: {
    modelValue: { type: Array, default: () => [] },
    name: { type: String, default: '' },
  },

  emits: ['update:modelValue', 'change', 'input'],

  components: {
    'input-multipunch': InputMultipunch,
  },

  template: `
<div class="apqa-input-qcrule-marks">
  <input-multipunch
    :model-value="modelValue"
    :options="MARKERS"
    :placeholder="'Select markers…'"
    :name="name"
    @update:model-value="onModelUpdate"
    @change="onChange"
  />
</div>
`,

  setup(props, { emit }) {
    function onModelUpdate(value) {
      emit('update:modelValue', value);
    }

    function onChange(value) {
      emit('change', value);
      emit('input', value);
    }

    return { MARKERS, onModelUpdate, onChange };
  },
};

export default InputQcruleMarks;
