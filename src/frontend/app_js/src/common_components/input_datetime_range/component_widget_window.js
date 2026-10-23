
import { createApp, ref, reactive, nextTick, onMounted } from 'vue';
import logErr from '../_log_error_proxy';



function hasValue(value) {
  if( typeof value==='number' )
    return true;
  else if( typeof value==='string' )
    return !(/^\s*$/.test(value))
  else
    return !!value;
}

// Native <input type="datetime-local"> values are local-time strings in the
// `YYYY-MM-DDTHH:mm` form. The app represents dates as `Date` objects, so we
// convert at this DOM boundary only.
function toLocalInputValue(value) {
  if (!(value instanceof Date) || Number.isNaN(value.getTime())) {
    return '';
  }
  const pad = (n) => String(n).padStart(2, '0');
  return (
    `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}` +
    `T${pad(value.getHours())}:${pad(value.getMinutes())}`
  );
}

function fromLocalInputValue(value) {
  if (typeof value !== 'string' || !value.trim()) {
    return null;
  }
  const date = new Date(value.trim());
  return Number.isNaN(date.getTime()) ? null : date;
}




const mountToComponent = (targetEl,outerResolve,outerReject,oldValue,validationCb) => {
  const internalPromiseContext = {
    resolve: () => { throw new Error('promise not inited'); },
    reject: () => { throw new Error('promise not inited'); },
    promise: null,
  };
  internalPromiseContext.promise = new Promise((resolve,reject) => {
    internalPromiseContext.resolve = resolve;
    internalPromiseContext.reject = reject;
  });
  internalPromiseContext.promise.then(
    outerResolve,
    outerReject,
  );
  const widget = createApp({
    template: `
<form  @submit.prevent="handleSubmit" :class="\`\${isBusy ? 'mdmreport-form-busy' : ''}\`">
  <div class="error form-validation-error">{{ error }}</div>
  <div class="error form-validation-error">{{ validationaFailureMsg }}</div>
  <fieldset class="mdmreport-controls line1">
    From
    <input
      type="datetime-local"
      class="mdmreport-control"
      v-model="formFields.from"
      ref="refInputLow"
    />
    to
    <input
      type="datetime-local"
      class="mdmreport-control"
      v-model="formFields.to"
      ref="refInputHigh"
    />.
  </fieldset>
  <fieldset class="mdmreport-controls line2">
    <button type="submit" class="apqa-button-close apqa-button-close-submit">Select</Button>
    <button type="button" class="apqa-button-close apqa-button-close-cancel" @click.prevent="handleCancel">Cancel</Button>
  </fieldset>
</form>
`,
    setup() {

      const error = ref('');
      const validationaFailureMsg = ref('');
      const isBusy = ref(false);

      const refInputLow = ref(null);
      const refInputHigh = ref(null);

      const formFields = reactive({
        from: toLocalInputValue(oldValue?.from),
        to: toLocalInputValue(oldValue?.to),
      });

      const handleCancel = async () => {
        internalPromiseContext.reject(null);
      };

      const handleSubmit = async () => {
        try {
          isBusy.value = true;
          const range = {
            from: fromLocalInputValue(formFields.from),
            to: fromLocalInputValue(formFields.to),
          };
          const validationFailure = validationCb(range); // expected to return error message or null
          if( validationFailure ) {
            validationaFailureMsg.value = validationFailure;
            return;
          } else
            internalPromiseContext.resolve(range);
        } catch (error) {
          if(error instanceof Error) {
            error.value = error;
            logErr('Error in datetime range picker component');
            logErr(error);
          } else {
            /* rejected - means "cancel" - ok */
          }
        } finally {
          isBusy.value = false;
        }
      };

      const focusInput = async () => {
        await nextTick();
        const shouldTargetHigh =
          hasValue(formFields.to) &&
          !hasValue(formFields.from);
        if (shouldTargetHigh) {
          refInputHigh.value?.focus();
        } else {
          refInputLow.value?.focus();
        }
      };

      onMounted(async () => {
        await Promise.all([
          focusInput(),
        ])
      });

      return {
        formFields,
        handleSubmit,
        handleCancel,
        isBusy,
        validationaFailureMsg,
        error,
        refInputLow,
        refInputHigh,
      };
    },
  });
  internalPromiseContext.promise.finally(()=>{ widget.unmount(); });
  widget.mount(targetEl);
};

export default mountToComponent;
