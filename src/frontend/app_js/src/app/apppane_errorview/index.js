import './style.css';
import ComponentFormatDatetime from '@/common_components/format_datetime/index';

const ErrorView = {
  props: ['errors'],

  components: {
    'component-format-datetime': ComponentFormatDatetime,
  },

  template: `
<div
  class="apqa-error-banner"
  :class="{ 'apqa-error-banner-nonempty': errors.length > 0 }"
  role="alert"
  aria-live="assertive"
>
  <div v-for="err in errors" :key="err.id" class="apqa-error-banner-item">
    <span class="apqa-error-banner-item-time"><component-format-datetime :dt="err.time" /></span>
    <span class="apqa-error-banner-item-body">{{ message(err.error) }}</span>
  </div>
</div>
`,

  setup() {
    // The global list may hold any value `logError` was given, not just `Error`
    // instances, so render each line safely instead of assuming `.message` exists.
    function message(error) {
      return error?.message ?? String(error);
    }
    return { message };
  },
};

export default ErrorView;
