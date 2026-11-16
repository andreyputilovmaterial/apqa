import './rule_delete_confirm.css';

// Confirmation dialog shown before deleting a QC rule. It is opened through the
// modal system (`createModal`), so it receives `resolve`/`reject` plus the
// `record` to delete. "Delete" resolves `true`; Cancel (and the backdrop close)
// reject, mirroring the RuleForm contract.
const RuleDeleteConfirm = {
  props: ['resolve', 'reject', 'record', 'kind'],

  template: `
<div class="apqa-modal-form apqa-rule-delete-confirm">
  <p class="apqa-rule-delete-confirm-text">
    Delete {{ kind }} <span class="apqa-rule-delete-confirm-name">{{ record.name }}</span>?
    This cannot be undone.
  </p>
  <div class="apqa-modal-actions">
    <button type="button" class="apqa-button-close apqa-button-danger" @click="confirm">Delete</button>
    <button type="button" class="apqa-button-close" @click="cancel">Cancel</button>
  </div>
</div>
`,

  setup(props) {
    const kind = props.kind || 'rule';

    function confirm() {
      props.resolve(true);
    }

    function cancel() {
      props.reject();
    }

    return { kind, confirm, cancel };
  },
};

export default RuleDeleteConfirm;
