
// import { Vue } from "./vue.js";
import { createApp } from 'vue';


import './app.css';
import './app_form_control_adjustments.css';


// all from "common_components"
import ComponentSectionRollup from './common_components/rollable_sections/index';
import ComponentTabbedPanes from './common_components/tabbed_panes/tabbed_panes';
import ComponentTabbedPane from './common_components/tabbed_panes/tabbed_pane';
import ComponentFilterRecordsForm from './common_components/filter_records_form/index';
import ComponentFormatDatetime from './common_components/display/format_datetime/index';
import ComponentFormatFilesize from './common_components/display/format_filesize/index';
import ComponentFormatHash from './common_components/display/format_hash/index';
import ComponentFormatLocalFilePath from './common_components/display/format_local_file_path/index';
import ComponentInputNumericRange from './common_components/input_types/numeric_range/index';
import ComponentInputDatetimeRange from './common_components/input_types/datetime_range/index';
import ComponentInputMultipunch from './common_components/input_types/multipunch/index';
import ComponentInputRegexText from './common_components/input_types/regex_text/index';
import ComponentInputQcruleTags from './common_components/input_types/qcrules/tags/index';
import ComponentInputQcruleMarks from './common_components/input_types/qcrules/marks/index';
import ComponentInputSearchSelect from './common_components/input_types/search_select/index';
import ComponentLoaderSpinner from './common_components/display/loader_spinner/index';
import ComponentLoaderInProgress from './common_components/display/loader_inprogress/index';
import { registerCmdletComponents } from './common_components/cmdlet_components/index';
import { registerInputCmdletComponents } from './common_components/input_types/cmdlets/index';
import './common_components/css_grid/styles.css';

// all "system" components - modals and the environment for showing errors...
import { ModalsSite } from './common_components/modals/modals';
import ManipulateNavLinksDummyWrapper from './app/background_navlinks_attachmodals/manipulate_links';

// app-specific views and features
import ErrorView from './app/apppane_errorview/index';
import OnlineMonitor from './app/background_onlineindicator/index';
import QcRulesList from './app/qcrules_list/index';
import ProjectHeaderPopulator from './app/project_settings/populator';
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
  <project-header-populator></project-header-populator>
  <modals-site></modals-site>
  <background-online-indicator></background-online-indicator>
</div>
`,
    components: {
      'errorbanner': ErrorView,
      'background-online-indicator': OnlineMonitor,
      'component-qcrules-list': QcRulesList,
      'background-navlinks-attachmodals': ManipulateNavLinksDummyWrapper,
      'project-header-populator': ProjectHeaderPopulator,
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
  app.component('component-input-multipunch', ComponentInputMultipunch);
  app.component('component-input-regextext', ComponentInputRegexText);
  app.component('component-input-search-select', ComponentInputSearchSelect);
  app.component('component-input-qcrule-tags', ComponentInputQcruleTags);
  app.component('component-input-qcrule-marks', ComponentInputQcruleMarks);
  app.component('component-loader-spinner', ComponentLoaderSpinner);
  app.component('component-loader-inprogress', ComponentLoaderInProgress);
  registerCmdletComponents(app);
  registerInputCmdletComponents(app);
  app.mount('#ui_app');





});
