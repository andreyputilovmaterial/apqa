import './rule_error_trace.css';

// Minimal read-only modal shown when the short error message on a rule card is
// clicked. Opened through the modal system (`createModal`), so it receives
// `resolve`/`reject` plus the `traceback` text to show. Close (and the backdrop
// click) simply dismiss it; there is no return value.
const RuleErrorTrace = {
  props: ['resolve', 'reject', 'traceback'],

  template: `
<div class="apqa-modal-form apqa-rule-error-trace">
  <h2>Rule error</h2>
  <p class="apqa-modal-form-subtitle">Full stack trace</p>
  <pre class="apqa-rule-error-trace-pre">{{ traceback }}</pre>
  <div class="apqa-modal-actions">
    <button type="button" class="apqa-button-close" @click="close">Close</button>
  </div>
</div>
`,

  setup(props) {
    function close() {
      props.resolve();
    }

    return { close };
  },
};

export default RuleErrorTrace;
