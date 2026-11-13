import InputGallery from '@/common_components/input_gallery/index';

import './styles.css';

// Modal host for the reusable input gallery. It is opened directly (not via an
// iframe) from the "Test page" navbar link.
const TestPageModal = {
  props: ['resolve', 'reject'],

  components: {
    'input-gallery': InputGallery,
  },

  template: `
<div class="apqa-modal-form apqa-testpage-form">
  <div class="apqa-testpage-form-header">
    <h2 class="apqa-testpage-form-title">Test page</h2>
    <p class="apqa-modal-form-subtitle apqa-testpage-form-subtitle">All form controls and their combinations, for visual verification.</p>
  </div>
  <div class="apqa-testpage-form-body">
    <input-gallery></input-gallery>
  </div>
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

export default TestPageModal;
