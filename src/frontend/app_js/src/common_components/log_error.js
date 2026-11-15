
export const logErrorContext = {
  promiseResolve: () => { throw new Error('logError: resolve(): promise not inited'); },
  promiseReject: () =>  { throw new Error('logError: reject(): promise not inited'); },
};
const promise = new Promise((resolve,reject) => {
  logErrorContext.promiseResolve = resolve;
  logErrorContext.promiseReject  = reject;
});
function logError(...args) {
  promise.then(logError=>logError(...args));
}
export default logError;
