import { makeComparisonOp } from './shared';

// The "full" (verbose) display of a comparison op: the op name unless the op
// declares a `full` display spec.
export default makeComparisonOp('full');
