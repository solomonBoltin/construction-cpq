import { useEffect, useRef } from 'react';

/**
 * Hook for step-based data fetching that runs only once per mount.
 * This prevents duplicate API calls in React Strict Mode and ensures
 * fresh data when navigating back to a step.
 */
export const useStepFetch = (fetchFn: () => Promise<void> | void) => {
  const hasFetched = useRef(false);

  useEffect(() => {
    if (hasFetched.current) return;
    
    hasFetched.current = true;
    const result = fetchFn();
    
    // Handle async fetch functions
    if (result instanceof Promise) {
      result.catch(error => {
        console.error('Step fetch error:', error);
        // Reset flag on error so it can retry on next mount
        hasFetched.current = false;
      });
    }
    
    // Cleanup function to reset flag when component unmounts
    return () => {
      hasFetched.current = false;
    };
    
    // Intentionally empty dependency array - run only on mount
  }, []);
};
