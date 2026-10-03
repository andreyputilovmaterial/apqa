


import useDebuggingVars from './tasks/debugging_vars';
import useGitCommandsPerfMonitor from './tasks/git_commands_perf_monitor';
import useCheckException from './tasks/exception_check';
import useAppBackendWarnings from './tasks/backend_warnings';


const tasks = [
    useDebuggingVars,
    useGitCommandsPerfMonitor,
    useCheckException,
    useAppBackendWarnings,
];


function useTasks(args) {

    const exports = {};
    const repoActions = {};
    const repoStatus = {};

    for( const task of tasks) {
        Promise.resolve().then(() => {
            try {
                const taskAddedMethods = task({...args.exports,...exports,repoActions:{...args.repoActions,...repoActions},repoStatus:{...args.repoStatus,...repoStatus}});
                Object.assign(repoActions,taskAddedMethods.repoActions);
                Object.assign(repoStatus,taskAddedMethods.repoStatus);
                Object.assign(exports,taskAddedMethods);
            } catch(e) {
                if( !!args?.repoActions?.logError )
                    args.repoActions.logError(`maintenance-n-debug task failed: ${e}`);
                else
                    console.error(`WARNING: maintenance-n-debug task failed, but there is no "logError" initialized in repoActions; "logError" should be added to "exports" before calling "maintenanceDebug" tasks.`);
                throw e;
            }
        });
    }

    return ({
        ...exports,
        repoStatus,
        repoActions,
    });

}

export default useTasks;


