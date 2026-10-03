
import { ref, onMounted, onUnmounted, } from 'vue';

const randomJitter = () => Math.floor(Math.random()*200-100);
const ISONLINE_TIMER_INTERVAL = 7850 +  + randomJitter()



function useIsOnline() {

    const isOnline = ref(true);
    const isOnlinePollingTimer = ref(undefined);

    async function setIsOnlineTimer() {
        try {
            const fn = async function () {
                try {
                    const response = await fetch('/functionality/isup.txt',{method:'HEAD'});
                    isOnline.value = response.ok;
                } catch(e) {
                    if( !!repoActions?.logError )
                        repoActions.logError(`isOnline polling task failed: ${e}`);
                    else
                        console.error(`WARNING: isOnline polling task failed, but there is no "logError" initialized in repoActions; "logError" should be added to "exports" before calling "isOnline" tasks.`);
                    throw e;
                }
            }
            isOnlinePollingTimer.value = setInterval(fn,ISONLINE_TIMER_INTERVAL);
        } catch(e) {
            if( !!repoActions?.logError )
                repoActions.logError(`isOnline polling task failed: ${e}`);
            else
                console.error(`WARNING: isOnline polling task failed, but there is no "logError" initialized in repoActions; "logError" should be added to "exports" before calling "isOnline" tasks.`);
            throw e;
        }
    }

    onMounted( setIsOnlineTimer );

    onUnmounted( () => new Promise( resolve => resolve(clearInterval(isOnlinePollingTimer.value))) );

    return ({
        repoStatus: {},
        repoActions: {},
        isOnline,
    });

}

export default useIsOnline;

