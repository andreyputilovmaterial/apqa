import { reactive } from 'vue';

import { logErrorContext } from '@/common_components/log_error';
import { genId } from '@/common_defs/helper_functions';

function useErrorReporting() {
  const errors = reactive([]);

  function logError(e) {
    const timestamp = new Date();
    errors.push({
      error: e,
      id: genId([errors.length, timestamp]),
      time: timestamp,
    });
    console.error(e);
  }

  // Resolve the deferred logger in `log_error` so that anything logged through
  // `logError` before this composable was initialized is now delivered to the
  // banner (and to the console).
  logErrorContext.promiseResolve(logError);

  return {
    errors,
  };
}

export default useErrorReporting;
