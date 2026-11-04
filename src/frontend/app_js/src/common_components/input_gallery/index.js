import { ref } from 'vue';

import FormField from '../form_field/index';
import InputNumericRange from '../input_numeric_range/index';
import InputDatetimeRange from '../input_datetime_range/index';
import InputMultipunch from '../input_multipunch/index';
import InputSearchSelect from '../input_search_select/index';

import './styles.css';

// A visual catalog of every form control — native inputs plus the reusable apqa
// input components — so they can all be checked in one place. Each control is
// shown with a label, and related controls are grouped into sections.
const InputGallery = {
  components: {
    'form-field': FormField,
    'input-numeric-range': InputNumericRange,
    'input-datetime-range': InputDatetimeRange,
    'input-multipunch': InputMultipunch,
    'input-search-select': InputSearchSelect,
  },

  setup() {
    const numericRange = ref({ from: 1983, to: 2005 });
    const datetimeRange = ref({
      from: new Date('2025-01-01T08:00:00'),
      to: new Date('2025-12-31T18:00:00'),
    });
    const searchSelect = ref('alpha');
    const multipunch = ref(['alpha', 'gamma']);

    const selectOptions = [
      { value: 'alpha', label: 'Alpha' },
      { value: 'beta', label: 'Beta' },
      { value: 'gamma', label: 'Gamma' },
    ];

    return {
      numericRange,
      datetimeRange,
      searchSelect,
      multipunch,
      selectOptions,
    };
  },

  template: `
<div class="apqa-input-gallery">

  <section class="apqa-input-gallery-section">
    <h3 class="apqa-input-gallery-section-title">Text inputs</h3>
    <div class="apqa-input-gallery-fields">
      <form-field label="Text (label on top)">
        <input type="text" name="text-top" placeholder="Type here" />
      </form-field>
      <form-field label="Text (label beside)" label-position="left">
        <input type="text" name="text-left" placeholder="Type here" />
      </form-field>
      <form-field label="Text (full width)" help="Fills the whole field.">
        <input type="text" class="apqa-input-fullwidth" name="text-fullwidth" />
      </form-field>
      <form-field label="Text (required)" required>
        <input type="text" class="apqa-input-fullwidth" name="text-required" />
      </form-field>
      <form-field label="Text (disabled)">
        <input type="text" class="apqa-input-fullwidth" name="text-disabled" value="Disabled value" disabled />
      </form-field>
      <form-field label="Text (readonly)">
        <input type="text" class="apqa-input-fullwidth" name="text-readonly" value="Readonly value" readonly />
      </form-field>
      <form-field label="Textarea" help="Multi-line text.">
        <textarea class="apqa-input-fullwidth" name="textarea" rows="4"></textarea>
      </form-field>
      <form-field label="Password">
        <input type="password" class="apqa-input-fullwidth" name="password" />
      </form-field>
      <form-field label="Email">
        <input type="email" class="apqa-input-fullwidth" name="email" placeholder="name@example.com" />
      </form-field>
      <form-field label="URL">
        <input type="url" class="apqa-input-fullwidth" name="url" placeholder="https://" />
      </form-field>
      <form-field label="Telephone">
        <input type="tel" class="apqa-input-fullwidth" name="tel" />
      </form-field>
      <form-field label="Search">
        <input type="search" class="apqa-input-fullwidth" name="search" />
      </form-field>
    </div>
  </section>

  <section class="apqa-input-gallery-section">
    <h3 class="apqa-input-gallery-section-title">Numbers</h3>
    <div class="apqa-input-gallery-fields">
      <form-field label="Number">
        <input type="number" name="number" />
      </form-field>
      <form-field label="Number (min/max/step)" help="Min 0, max 100, step 5.">
        <input type="number" name="number-range" min="0" max="100" step="5" />
      </form-field>
      <form-field label="Number (full width)">
        <input type="number" class="apqa-input-fullwidth" name="number-fullwidth" />
      </form-field>
    </div>
  </section>

  <section class="apqa-input-gallery-section">
    <h3 class="apqa-input-gallery-section-title">Date &amp; time</h3>
    <div class="apqa-input-gallery-fields">
      <form-field label="Date">
        <input type="date" name="date" />
      </form-field>
      <form-field label="Date &amp; time (local)">
        <input type="datetime-local" name="datetime-local" />
      </form-field>
      <form-field label="Time">
        <input type="time" name="time" />
      </form-field>
      <form-field label="Month">
        <input type="month" name="month" />
      </form-field>
      <form-field label="Week">
        <input type="week" name="week" />
      </form-field>
    </div>
  </section>

  <section class="apqa-input-gallery-section">
    <h3 class="apqa-input-gallery-section-title">Ranges</h3>
    <div class="apqa-input-gallery-fields">
      <form-field label="Range slider" help="Native type=range.">
        <input type="range" class="apqa-input-fullwidth" name="range-slider" min="0" max="100" step="1" />
      </form-field>
      <form-field label="Numeric range" help="Reusable input-numeric-range component.">
        <input-numeric-range v-model="numericRange" class="apqa-input-fullwidth" />
      </form-field>
      <form-field label="Datetime range" help="Reusable input-datetime-range component.">
        <input-datetime-range v-model="datetimeRange" class="apqa-input-fullwidth" />
      </form-field>
    </div>
  </section>

  <section class="apqa-input-gallery-section">
    <h3 class="apqa-input-gallery-section-title">File picker</h3>
    <div class="apqa-input-gallery-fields">
      <form-field label="File">
        <input type="file" name="file" />
      </form-field>
      <form-field label="File (multiple)">
        <input type="file" name="file-multiple" multiple />
      </form-field>
    </div>
  </section>

  <section class="apqa-input-gallery-section">
    <h3 class="apqa-input-gallery-section-title">Selects</h3>
    <div class="apqa-input-gallery-fields">
      <form-field label="Select">
        <select name="select">
          <option value="alpha">Alpha</option>
          <option value="beta">Beta</option>
          <option value="gamma">Gamma</option>
        </select>
      </form-field>
      <form-field label="Select (multiple)">
        <select name="select-multiple" multiple size="3">
          <option value="alpha">Alpha</option>
          <option value="beta">Beta</option>
          <option value="gamma">Gamma</option>
        </select>
      </form-field>
      <form-field label="Search select" help="Reusable input-search-select component.">
        <input-search-select v-model="searchSelect" :options="selectOptions" placeholder="Choose..." />
      </form-field>
      <form-field label="Multipunch" help="Reusable input-multipunch component.">
        <input-multipunch v-model="multipunch" :options="selectOptions" placeholder="Choose..." />
      </form-field>
    </div>
  </section>

  <section class="apqa-input-gallery-section">
    <h3 class="apqa-input-gallery-section-title">Checkboxes</h3>
    <div class="apqa-input-gallery-fields">
      <form-field label="Single checkbox">
        <label class="apqa-input-option"><input type="checkbox" name="single-check" /> Enable feature</label>
      </form-field>
      <form-field label="Checkbox group (vertical)">
        <div class="apqa-input-options">
          <label class="apqa-input-option"><input type="checkbox" name="check-group" value="a" checked /> Option A</label>
          <label class="apqa-input-option"><input type="checkbox" name="check-group" value="b" /> Option B</label>
          <label class="apqa-input-option"><input type="checkbox" name="check-group" value="c" /> Option C</label>
        </div>
      </form-field>
      <form-field label="Checkbox group (inline)">
        <div class="apqa-input-options apqa-input-options-inline">
          <label class="apqa-input-option"><input type="checkbox" name="check-group-inline" value="a" checked /> A</label>
          <label class="apqa-input-option"><input type="checkbox" name="check-group-inline" value="b" /> B</label>
          <label class="apqa-input-option"><input type="checkbox" name="check-group-inline" value="c" /> C</label>
        </div>
      </form-field>
    </div>
  </section>

  <section class="apqa-input-gallery-section">
    <h3 class="apqa-input-gallery-section-title">Radio buttons</h3>
    <div class="apqa-input-gallery-fields">
      <form-field label="Radio group (vertical)">
        <div class="apqa-input-options">
          <label class="apqa-input-option"><input type="radio" name="radio-group" value="a" checked /> Option A</label>
          <label class="apqa-input-option"><input type="radio" name="radio-group" value="b" /> Option B</label>
          <label class="apqa-input-option"><input type="radio" name="radio-group" value="c" /> Option C</label>
        </div>
      </form-field>
      <form-field label="Radio group (inline)">
        <div class="apqa-input-options apqa-input-options-inline">
          <label class="apqa-input-option"><input type="radio" name="radio-group-inline" value="a" checked /> A</label>
          <label class="apqa-input-option"><input type="radio" name="radio-group-inline" value="b" /> B</label>
          <label class="apqa-input-option"><input type="radio" name="radio-group-inline" value="c" /> C</label>
        </div>
      </form-field>
    </div>
  </section>

  <section class="apqa-input-gallery-section">
    <h3 class="apqa-input-gallery-section-title">Other</h3>
    <div class="apqa-input-gallery-fields">
      <form-field label="Color">
        <input type="color" name="color" value="#385000" />
      </form-field>
      <form-field label="Toggle / switch">
        <label class="apqa-input-switch">
          <input type="checkbox" name="toggle" checked />
          <span class="apqa-input-switch-track"><span class="apqa-input-switch-thumb"></span></span>
        </label>
      </form-field>
    </div>
  </section>

  <section class="apqa-input-gallery-section">
    <h3 class="apqa-input-gallery-section-title">Buttons</h3>
    <div class="apqa-input-gallery-fields">
      <form-field label="Button">
        <button type="button" class="apqa-input-button">Default</button>
      </form-field>
      <form-field label="Primary button">
        <button type="button" class="apqa-input-button apqa-input-button-primary">Primary</button>
      </form-field>
      <form-field label="Disabled button">
        <button type="button" class="apqa-input-button" disabled>Disabled</button>
      </form-field>
      <form-field label="Submit / reset">
        <input type="submit" class="apqa-input-button" value="Submit" />
        <input type="reset" class="apqa-input-button" value="Reset" />
      </form-field>
    </div>
  </section>

</div>
`,
};

export default InputGallery;
