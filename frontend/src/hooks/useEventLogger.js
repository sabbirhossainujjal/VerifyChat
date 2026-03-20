import { useCallback } from 'react';
import { logEvent } from '../services/api';

export function useEventLogger(sessionId) {
  const log = useCallback((eventType, eventData = {}) => {
    if (!sessionId) return;
    logEvent(sessionId, eventType, eventData).catch(() => {});
  }, [sessionId]);
  return log;
}
