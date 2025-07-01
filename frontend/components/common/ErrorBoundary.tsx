import React, { ReactNode } from 'react';
import { ErrorBoundary as ReactErrorBoundary } from 'react-error-boundary';

interface ErrorFallbackProps {
  error: Error;
  resetErrorBoundary: () => void;
  level?: 'app' | 'page' | 'component';
}

const ErrorFallback: React.FC<ErrorFallbackProps> = ({ error, resetErrorBoundary, level = 'component' }) => {
  const getMessage = () => {
    switch (level) {
      case 'app': return 'The application encountered an unexpected error';
      case 'page': return 'This page encountered an error';
      default: return 'This component encountered an error';
    }
  };

  return (
    <div className="min-h-[200px] flex items-center justify-center p-6">
      <div className="text-center max-w-md">
        <div className="text-red-600 mb-4">
          <svg className="w-16 h-16 mx-auto" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-slate-800 mb-2">{getMessage()}</h2>
        <p className="text-slate-600 mb-4">{error.message}</p>
        <button
          onClick={resetErrorBoundary}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    </div>
  );
};

export const AppErrorBoundary: React.FC<{ children: ReactNode }> = ({ children }) => (
  <ReactErrorBoundary
    FallbackComponent={(props) => <ErrorFallback {...props} level="app" />}
    onError={(error, info) => console.error('App Error:', error, info)}
  >
    {children}
  </ReactErrorBoundary>
);

export const PageErrorBoundary: React.FC<{ children: ReactNode }> = ({ children }) => (
  <ReactErrorBoundary
    FallbackComponent={(props) => <ErrorFallback {...props} level="page" />}
    onError={(error, info) => console.error('Page Error:', error, info)}
  >
    {children}
  </ReactErrorBoundary>
);

export const ComponentErrorBoundary: React.FC<{ children: ReactNode }> = ({ children }) => (
  <ReactErrorBoundary
    FallbackComponent={(props) => <ErrorFallback {...props} level="component" />}
    onError={(error, info) => console.error('Component Error:', error, info)}
  >
    {children}
  </ReactErrorBoundary>
);
