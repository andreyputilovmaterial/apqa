



function useBackendWarnings({repoStatus,repoActions,...exports}) {
    const logErrorWrapper = msg => {
        if( !!repoActions?.logError )
            repoActions.logError(`backendWarnings task failed: ${e}`);
        else
            console.error(`WARNING: backendWarnings task failed, but there is no "logError" initialized in repoActions; "logError" should be added to "exports" before calling "backendWarnings" tasks.`);
    };
    const config = repoStatus.config;
    if( !config ) {
        const msg = `please init "config" first before calling backendWarnings, please check the order of scritps in app setup`;
        logErrorWrapper(msg);
        throw new Error(msg);
    }
    watch(
        ()=>config,
        () => {
            const config = repoStatus.config;
        },
    );
}

export default useBackendWarnings;
