

import { ref, onMounted, onUnmounted, } from 'vue';


const randomJitter = () => Math.floor(Math.random()*200-100);
const updateInterval = 9000 + randomJitter();




function useGitCommandsPerfMonitor({repoStatus,repoActions,...exports}) {
    gitCommandsPerfIssuesCheckingTimer = ref(undefined);

    function init() {
        try {
            const gitCommandConcurrencyManager = exports?.gitCommandConcurrencyManager;
            if( !gitCommandConcurrencyManager )
                throw new Error(`gitCommandsPerfMonitor: missing gitCommandConcurrencyManager, this should be inited first, please check the order of scripts in app setup`);
            gitCommandsPerfIssuesCheckingTimer.value = setInterval(
                ()=>{
                    try {
                        const recentCommandsMinDelay = gitCommandConcurrencyManager.getPerformanceMetric('recent-tasks-min-delay')();
                        if( (+recentCommandsMinDelay)>10000 ) {
                            const warnRecordId = 'git-command-perf-warning';
                            const timestamp = new Date();
                            const warnMsg = `Warning: performance issues while executing git commands, some take up to ${((+recentCommandsMinDelay)/1000)|0} seconds, or more (alerted ${timestamp})`;
                            const warnRecordsMatchingId = errors.value.filter(e=>e.id===warnRecordId);
                            const warnRecordObject = warnRecordsMatchingId.length>0 ? warnRecordsMatchingId[0] : ({
                                id: warnRecordId,
                                time: timestamp,
                            });
                            warnRecordObject.error = warnMsg;
                            if( warnRecordsMatchingId.length===0 ) // if not added before, append a new record; or, existing one was updated
                                errors.value.push(warnRecordObject);
                        }
                    } catch(e) {
                        if( !!repoActions?.logError )
                            repoActions.logError(`gitCommandsPerfMonitor task failed: ${e}`);
                        else
                            console.error(`WARNING: gitCommandsPerfMonitor task failed, but there is no "logError" initialized in repoActions; "logError" should be added to "exports" before calling "gitCommandsPerfMonitor" tasks.`);
                        throw e;
                    }
                },
                updateInterval,
            );
        } catch(e) {
            if( !!repoActions?.logError )
                repoActions.logError(`gitCommandsPerfMonitor task failed: ${e}`);
            else
                console.error(`WARNING: gitCommandsPerfMonitor task failed, but there is no "logError" initialized in repoActions; "logError" should be added to "exports" before calling "gitCommandsPerfMonitor" tasks.`);
            throw e;
        }
    }

    onMounted( init );

    onUnmounted( () => new Promise( resolve => resolve(clearInterval(gitCommandsPerfIssuesCheckingTimer.value))) );

}

export default useGitCommandsPerfMonitor;
