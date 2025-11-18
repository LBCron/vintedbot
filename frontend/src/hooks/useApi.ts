/**
 * Generic API hook for data fetching with loading and error states
 */
import { useState, useEffect, useCallback, useRef } from 'react';

interface UseApiOptions<T> {
  immediate?: boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
}

interface UseApiReturn<T, P extends any[]> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  execute: (...args: P) => Promise<T | null>;
  reset: () => void;
}

export function useApi<T, P extends any[] = []>(
  apiFunction: (...args: P) => Promise<{ data: T }>,
  options: UseApiOptions<T> = {}
): UseApiReturn<T, P> {
  const { immediate = false, onSuccess, onError } = options;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState<Error | null>(null);

  // HIGH BUG FIX #4: Use refs to store latest values without triggering re-renders
  // This prevents execute callback from being recreated on every parent render
  const apiFunctionRef = useRef(apiFunction);
  const onSuccessRef = useRef(onSuccess);
  const onErrorRef = useRef(onError);

  // Update refs on each render to capture latest values
  useEffect(() => {
    apiFunctionRef.current = apiFunction;
    onSuccessRef.current = onSuccess;
    onErrorRef.current = onError;
  });

  const execute = useCallback(
    async (...args: P): Promise<T | null> => {
      try {
        setLoading(true);
        setError(null);

        const response = await apiFunctionRef.current(...args);
        const responseData = response.data;

        setData(responseData);
        onSuccessRef.current?.(responseData);

        return responseData;
      } catch (err) {
        const error = err instanceof Error ? err : new Error('An error occurred');
        setError(error);
        onErrorRef.current?.(error);

        return null;
      } finally {
        setLoading(false);
      }
    },
    [] // Empty deps - execute function is stable and uses latest values via refs
  );

  const reset = useCallback(() => {
    setData(null);
    setLoading(false);
    setError(null);
  }, []);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return { data, loading, error, execute, reset };
}
