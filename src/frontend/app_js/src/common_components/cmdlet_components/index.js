// Registration point for the display-only "cmdlet world" components. Every
// component here is read-only and is referenced from templates by its global
// tag (no per-file imports), which is what breaks the import cycle between
// `cmdlet_chain` and the nested-chain arg types.
import CmdletCompact from './cmdlet/compact';
import CmdletFull from './cmdlet/full';
import CmdletChainCompact from './cmdlet_chain/compact';
import CmdletChainFull from './cmdlet_chain/full';
import ComparisonOpCompact from './comparison_op/compact';
import ComparisonOpFull from './comparison_op/full';
import CmdletArgCompact from './cmdlet_arg/compact';
import CmdletArgFull from './cmdlet_arg/full';

import DataTypeTextCompact from './data_types/text/compact';
import DataTypeTextFull from './data_types/text/full';
import DataTypeNumberCompact from './data_types/number/compact';
import DataTypeNumberFull from './data_types/number/full';
import DataTypeBooleanCompact from './data_types/boolean/compact';
import DataTypeBooleanFull from './data_types/boolean/full';
import DataTypePathCompact from './data_types/path/compact';
import DataTypePathFull from './data_types/path/full';
import DataTypeOptionsCompact from './data_types/options/compact';
import DataTypeOptionsFull from './data_types/options/full';
import DataTypeListCompact from './data_types/list/compact';
import DataTypeListFull from './data_types/list/full';
import DataTypeJsonCompact from './data_types/json/compact';
import DataTypeJsonFull from './data_types/json/full';
import DataTypeCmdletChainCompact from './data_types/cmdlet_chain/compact';
import DataTypeCmdletChainFull from './data_types/cmdlet_chain/full';
import DataTypeCmdletChainsCompact from './data_types/cmdlet_chains/compact';
import DataTypeCmdletChainsFull from './data_types/cmdlet_chains/full';
import DataTypeDateCompact from './data_types/date/compact';
import DataTypeDateFull from './data_types/date/full';

export const cmdletComponents = {
  'component-cmdlet-compact': CmdletCompact,
  'component-cmdlet-full': CmdletFull,
  'component-cmdlet-chain-compact': CmdletChainCompact,
  'component-cmdlet-chain-full': CmdletChainFull,
  'component-comparison-op-compact': ComparisonOpCompact,
  'component-comparison-op-full': ComparisonOpFull,
  'component-cmdlet-arg-compact': CmdletArgCompact,
  'component-cmdlet-arg-full': CmdletArgFull,

  'component-cmdlet-arg-text-compact': DataTypeTextCompact,
  'component-cmdlet-arg-text-full': DataTypeTextFull,
  'component-cmdlet-arg-number-compact': DataTypeNumberCompact,
  'component-cmdlet-arg-number-full': DataTypeNumberFull,
  'component-cmdlet-arg-boolean-compact': DataTypeBooleanCompact,
  'component-cmdlet-arg-boolean-full': DataTypeBooleanFull,
  'component-cmdlet-arg-path-compact': DataTypePathCompact,
  'component-cmdlet-arg-path-full': DataTypePathFull,
  'component-cmdlet-arg-options-compact': DataTypeOptionsCompact,
  'component-cmdlet-arg-options-full': DataTypeOptionsFull,
  'component-cmdlet-arg-list-compact': DataTypeListCompact,
  'component-cmdlet-arg-list-full': DataTypeListFull,
  'component-cmdlet-arg-json-compact': DataTypeJsonCompact,
  'component-cmdlet-arg-json-full': DataTypeJsonFull,
  'component-cmdlet-arg-cmdlet-chain-compact': DataTypeCmdletChainCompact,
  'component-cmdlet-arg-cmdlet-chain-full': DataTypeCmdletChainFull,
  'component-cmdlet-arg-cmdlet-chains-compact': DataTypeCmdletChainsCompact,
  'component-cmdlet-arg-cmdlet-chains-full': DataTypeCmdletChainsFull,
  'component-cmdlet-arg-date-compact': DataTypeDateCompact,
  'component-cmdlet-arg-date-full': DataTypeDateFull,
};

export function registerCmdletComponents(app) {
  for (const [name, component] of Object.entries(cmdletComponents)) {
    app.component(name, component);
  }
}
