import { onMounted } from 'vue';

import logError from '@/common_components/_log_error_proxy';
import { fetchProjectInfo, applyProjectHeaderInfo } from './project_header';

// Fills the page-header project lines (database path, project name, description)
// and the document title from `GET /qc/project`. The header markup lives outside
// the Vue app, so this small component reaches into the DOM the same way the
// nav-links component already does.
const ProjectHeaderPopulator = {
  template: `<span class="apqa-project-header-populator"></span>`,

  setup() {
    onMounted(async () => {
      try {
        applyProjectHeaderInfo(await fetchProjectInfo());
      } catch (e) {
        logError(`Failed to load project header info: ${e}`);
      }
    });
  },
};

export default ProjectHeaderPopulator;
