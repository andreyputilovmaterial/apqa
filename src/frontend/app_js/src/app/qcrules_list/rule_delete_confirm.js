import './rule_delete_confirm.css';

// Confirmation dialog shown before deleting a QC rule. It is opened through the
// modal system (`createModal`), so it receives `resolve`/`reject` plus the
// `record` to delete. "Delete" resolves `true`; Cancel (and the backdrop close)
// reject, mirroring the RuleForm contract.
const RuleDeleteConfirm = {
  props: ['resolve', 'reject', 'record'],

  template: `
<div class="apqa-modal-form apqa-rule-delete-confirm">
  <p class="apqa-rule-delete-confirm-text">
    Delete rule <span class="apqa-rule-delete-confirm-name">{{ record.name }}</span>?
    This cannot be undone.
  </p>
  <div class="apqa-rule-delete-confirm-actions">
    <button type="button" class="apqa-rule-delete-confirm-button" @click="cancel">Cancel</button>
    <button type="button" class="apqa-rule-delete-confirm-button apqa-rule-delete-confirm-button-danger" @click="confirm">Delete</button>
  </div>
</div>
`,

  setup(props) {
    function confirm() {
      props.resolve(true);
    }

    function cancel() {
      props.reject();
    }

    return { confirm, cancel };
  },
};

export default RuleDeleteConfirm;
