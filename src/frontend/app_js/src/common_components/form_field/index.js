import './styles.css';

// Reusable labeled form-field wrapper: a label (above or beside the control),
// the control itself (passed via the default slot), and optional help text.
//
// It is intentionally presentation-only and does not force widths, so callers
// can choose natural-width vs full-width controls. `label-position="left"`
// renders the label beside the control instead of above it.
const FormField = {
  inheritAttrs: false,

  props: {
    label: { type: String, default: '' },
    labelPosition: { type: String, default: 'top' }, // 'top' | 'left'
    help: { type: String, default: '' },
    required: { type: Boolean, default: false },
    forId: { type: String, default: '' },
  },

  template: `
<div
  class="apqa-form-field"
  :class="{
    'apqa-form-field-label-left': labelPosition === 'left',
    'apqa-form-field-required': required
  }"
>
  <div class="apqa-form-field-body">
    <label v-if="label" class="apqa-form-field-label-text" :for="forId || null">
      {{ label }}<em v-if="required" class="apqa-form-field-required-mark">*</em>
    </label>
    <div class="apqa-form-field-control"><slot></slot></div>
  </div>
  <div v-if="help" class="apqa-form-field-help">{{ help }}</div>
</div>
`,
};

export default FormField;
