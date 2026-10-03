
// import { Vue } from "./vue.js";
import { createApp, ref, onMounted, onUnmounted, watch, reactive, h, } from 'vue'


import './app.css';
import './app_form_control_adjustments.css';

// global tools
import { genId, prettyprintBytes, makeFetchResponseErrorMessage, } from './common_defs/helper_functions';
import cliCommandRaw from './common_defs/cli';
import parseGitStatus from './common_defs/parse_git_status';
import ConcurrencyManager from './common_defs/concurrency/semaphore.js';
import ReplayEvent from './common_defs/concurrency/subscribe.js';

// "lib"
import { diff } from './lib/myers-diff/src/index';
import textconvBackend from './textconv_backend/index';
import textconvParseHeadersFromBackend from './textconv_backend/parse_headers';

// all from "common_components"
import ComponentSectionRollup from './common_components/rollable_sections/index';
import ComponentTabbedPanes from './common_components/tabbed_panes/tabbed_panes';
import ComponentTabbedPane from './common_components/tabbed_panes/tabbed_pane';
import ComponentFilterRecordsForm from './common_components/filter_records_form/index';
import ComponentFormatDatetime from './common_components/format_datetime/index';
import ComponentFormatFilesize from './common_components/format_filesize/index';
import ComponentFormatHash from './common_components/format_hash/index';
import ComponentFormatLocalFilePath from './common_components/format_local_file_path/index';
import ComponentInputNumericRange from './common_components/input_numeric_range/index';
import ComponentInputDatetimeRange from './common_components/input_datetime_range/index';
import ComponentLoaderSpinner from './common_components/loader_spinner/index';
import ComponentLoaderInProgress from './common_components/loader_inprogress/index';
import './common_components/css_grid/styles.css';

// all "system" components - modals, pages, environment for showing errors...
import { _logErrorProxyContext } from './common_components/_log_error_proxy';
import { ModalsSite, createModal } from './common_components/modals/modals';
import ManipulateNavLinksDummyWrapper from './app/background_navlinks_attachmodals/manipulate_links';

// direct children shown in starting view in app - window panes
import AppOnlineIndicator from './app/background_onlineindicator_overlay/index.js';
import ErrorView from './app/apppane_errorview/index';
import TerminalSessionView from './app/apppane_terminalview/index';
// direct children shown in starting view in app - tabs in main view
import RepoInitView from './app/window_repoinitview/init_repo';
import PageWelcome from './app/apptab_welcomeview/index';
import PageFiles from './app/apptab_filesview/index';
import PageHistory from './app/apptab_historyview/index';
import PageGitignore from './app/window_repoinitview/section_gitignore';
import PagePackcompression from './app/apptab_packcompression/index';

// functions and methods defined in app setup
import useCatFile from './common_app_exposed_defs/cat_file/index';
import useIsOnline from './common_app_exposed_defs/is_online/index';
import useMaintenanceDebug from './common_app_exposed_defs/maintenance_n_debug/index';






document.addEventListener("DOMContentLoaded", () => {

  // const { createApp, ref, onMounted, onUnmounted, toRaw } = Vue;



  const app = createApp({
    template: `
<div class="mdm-apqa-ui-app">
    Hey you
</div>
`,
    components: {
      'errorbanner': ErrorView,
    },
    setup() {

      const exports = {};

      return ({
        ...exports,
      });

    }
  })
  // FORCE VUE DEVTOOLS TO ACTIVATE
  app.config.performance = true;
  app.component('component-section-rollup', ComponentSectionRollup);
  app.component('component-tabbed-panes', ComponentTabbedPanes);
  app.component('component-tabbed-pane', ComponentTabbedPane);
  app.component('component-filter-records-form', ComponentFilterRecordsForm);
  app.component('component-format-datetime', ComponentFormatDatetime);
  app.component('component-format-filesize', ComponentFormatFilesize);
  app.component('component-format-hash', ComponentFormatHash);
  app.component('component-format-local-file-path', ComponentFormatLocalFilePath);
  app.component('component-input-numericrange',ComponentInputNumericRange);
  app.component('component-input-datetimerange',ComponentInputDatetimeRange);
  app.component('component-loader-spinner', ComponentLoaderSpinner);
  app.component('component-loader-inprogress', ComponentLoaderInProgress);
  app.mount('#ui_app');





});
