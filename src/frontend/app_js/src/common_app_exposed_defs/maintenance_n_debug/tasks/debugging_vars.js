
import { toRaw, version, isReactive, } from 'vue'


function useDebuggingVars({repoStatus}) {
    window.isReactive = isReactive;
    window.vueVersion = version;
    window.toRaw = toRaw;
    window.getRepoStatus = () => repoStatus.value;
    return {
        repoStatus: {},
        repoActions: {},
    };
}

export default useDebuggingVars;
