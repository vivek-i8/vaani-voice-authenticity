import { useEffect, useState, useCallback } from 'react';
import { checkBackendHealth } from './api';

export type BackendReachability = 'checking' | 'available' | 'unreachable';

export function useNetworkStatus() {
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== 'undefined' && typeof navigator.onLine === 'boolean'
      ? navigator.onLine
      : true
  );
  const [backendStatus, setBackendStatus] = useState<BackendReachability>('checking');

  const checkBackend = useCallback(async () => {
    if (!navigator.onLine) {
      setBackendStatus('unreachable');
      return;
    }
    const health = await checkBackendHealth(3000);
    setBackendStatus(health.ok ? 'available' : 'unreachable');
  }, []);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      void checkBackend();
    };
    const handleOffline = () => {
      setIsOnline(false);
      setBackendStatus('unreachable');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    void checkBackend();

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [checkBackend]);

  return { isOnline, backendStatus, recheckBackend: checkBackend };
}

