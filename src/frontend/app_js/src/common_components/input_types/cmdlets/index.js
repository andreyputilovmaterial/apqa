// Registration point for the cmdlet-editing components. Every component here is
// referenced from templates by its global tag (no per-file imports), which is
// what breaks the import cycle between `cmdlet_chain` and the nested-chain arg
// types.
import InputCmdlet from './cmdlet/index';
import InputCmdletChain from './cmdlet_chain/index';
import InputComparisonOp from './comparison_op/index';
import InputCmdletArg from './cmdlet_arg/index';

import InputArgText from './data_types/text/index';
import InputArgNumber from './data_types/number/index';
import InputArgBoolean from './data_types/boolean/index';
import InputArgPath from './data_types/path/index';
import InputArgOptions from './data_types/options/index';
import InputArgList from './data_types/list/index';
import InputArgJson from './data_types/json/index';
import InputArgCmdletChain from './data_types/cmdlet_chain/index';
import InputArgCmdletChains from './data_types/cmdlet_chains/index';
import InputArgDate from './data_types/date/index';

export const inputCmdletComponents = {
  'component-input-cmdlet': InputCmdlet,
  'component-input-cmdlet-chain': InputCmdletChain,
  'component-input-comparison-op': InputComparisonOp,
  'component-input-cmdlet-arg': InputCmdletArg,

  'component-input-cmdlet-arg-text': InputArgText,
  'component-input-cmdlet-arg-number': InputArgNumber,
  'component-input-cmdlet-arg-boolean': InputArgBoolean,
  'component-input-cmdlet-arg-path': InputArgPath,
  'component-input-cmdlet-arg-options': InputArgOptions,
  'component-input-cmdlet-arg-list': InputArgList,
  'component-input-cmdlet-arg-json': InputArgJson,
  'component-input-cmdlet-arg-cmdlet-chain': InputArgCmdletChain,
  'component-input-cmdlet-arg-cmdlet-chains': InputArgCmdletChains,
  'component-input-cmdlet-arg-date': InputArgDate,
};

export function registerInputCmdletComponents(app) {
  for (const [name, component] of Object.entries(inputCmdletComponents)) {
    app.component(name, component);
  }
}
