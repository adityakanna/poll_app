(function () {
    // Inactivity monitor service for authenticated pages.
    // The timer runs entirely in the background.
    const config = window.INACTIVITY_MONITOR_CONFIG || {};
    if (!config.enabled) {
        return;
    }

    const INACTIVITY_TIMEOUT_MS = Number(config.timeoutMs) || 15 * 60 * 1000;
    const LOGOUT_URL = config.logoutUrl || '/logout/?inactive=1';

    let inactivityTimer = null;
    let timerRunning = false;

    function clearInactivityTimer() {
        if (inactivityTimer) {
            clearTimeout(inactivityTimer);
            inactivityTimer = null;
        }
        timerRunning = false;
    }

    function logoutDueToInactivity() {
        clearInactivityTimer();
        clearAuthData();
        window.location.assign(LOGOUT_URL);
    }

    function scheduleInactivityLogout() {
        clearInactivityTimer();
        inactivityTimer = setTimeout(logoutDueToInactivity, INACTIVITY_TIMEOUT_MS);
        timerRunning = true;
    }

    function resetInactivityMonitor() {
        // User activity detected: cancel any running timer and start monitoring again.
        if (timerRunning) {
            clearInactivityTimer();
        }
        scheduleInactivityLogout();
    }

    function clearAuthData() {
        clearAuthCookies();
        clearAuthStorage();
    }

    function clearAuthCookies() {
        const cookieNames = ['sessionid', 'csrftoken'];
        cookieNames.forEach(name => {
            document.cookie = `${name}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax`;
            document.cookie = `${name}=; path=/; max-age=0; SameSite=Lax`;
        });
    }

    function clearAuthStorage() {
        [window.sessionStorage, window.localStorage].forEach(storage => {
            try {
                if (!storage) {
                    return;
                }
                const keysToRemove = [];
                for (let i = 0; i < storage.length; i += 1) {
                    const key = storage.key(i);
                    if (!key) {
                        continue;
                    }
                    const lowerKey = key.toLowerCase();
                    if (
                        lowerKey.includes('auth') ||
                        lowerKey.includes('session') ||
                        lowerKey.includes('token') ||
                        lowerKey.includes('login')
                    ) {
                        keysToRemove.push(key);
                    }
                }
                keysToRemove.forEach(key => storage.removeItem(key));
            } catch (error) {
                // Ignore storage access errors.
            }
        });
    }

    function onUserActivity(event) {
        if (event.type === 'visibilitychange' && document.visibilityState !== 'visible') {
            return;
        }
        resetInactivityMonitor();
    }

    function initializeInactivityMonitor() {
        const activityEvents = [
            'mousemove',
            'mousedown',
            'keydown',
            'touchstart',
            'scroll',
            'click',
            'change',
            'visibilitychange',
            'focus',
        ];

        activityEvents.forEach(eventName => {
            window.addEventListener(eventName, onUserActivity, {
                passive: true,
                capture: true,
            });
        });

        document.addEventListener('submit', onUserActivity, true);

        window.addEventListener('beforeunload', clearInactivityTimer);
        window.addEventListener('pagehide', clearInactivityTimer);

        scheduleInactivityLogout();
    }

    initializeInactivityMonitor();
})();
