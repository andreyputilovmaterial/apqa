
// import { Vue } from "./vue.js";
import { createApp } from 'vue';


import './app.css';
import './app_form_control_adjustments.css';


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
import ComponentMultipunch from './common_components/multipunch/index';
import ComponentLoaderSpinner from './common_components/loader_spinner/index';
import ComponentLoaderInProgress from './common_components/loader_inprogress/index';
import './common_components/css_grid/styles.css';

// all "system" components - modals, pages, environment for showing errors...
import { ModalsSite } from './common_components/modals/modals';
import ManipulateNavLinksDummyWrapper from './app/background_navlinks_attachmodals/manipulate_links';

// app-specific views and features
import ErrorView from './app/apppane_errorview/index';
import QcRulesList from './app/qcrules_list/index';
import useErrorReporting from './common_app_exposed_defs/error_reporting/index';






document.addEventListener("DOMContentLoaded", () => {

  // const { createApp, ref, onMounted, onUnmounted, toRaw } = Vue;



  const app = createApp({
    template: `
<div class="mdm-apqa-ui-app">
  <div class="apqa-app-section-errorbanner">
    <errorbanner :errors="errors"></errorbanner>
  </div>
  <div class="apqa-app-section-qcrules">
    <component-qcrules-list></component-qcrules-list>
  </div>
  <background-navlinks-attachmodals></background-navlinks-attachmodals>
  <modals-site></modals-site>
</div>
`,
    components: {
      'errorbanner': ErrorView,
      'component-qcrules-list': QcRulesList,
      'background-navlinks-attachmodals': ManipulateNavLinksDummyWrapper,
      'modals-site': ModalsSite,
    },
    setup() {
      const { errors } = useErrorReporting();

      return {
        errors,
      };
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
  app.component('component-multipunch', ComponentMultipunch);
  app.component('component-loader-spinner', ComponentLoaderSpinner);
  app.component('component-loader-inprogress', ComponentLoaderInProgress);
  app.mount('#ui_app');





});
