import { makeLiteralValueRenderer } from './shared';

// `literal-value` arg value — compact display (quotes text to keep its type
// unambiguous vs boolean/number).
export default makeLiteralValueRenderer();
