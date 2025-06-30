export class QuoteBuilderError extends Error {
  constructor(
    message: string,
    public code?: string,
    public originalError?: Error
  ) {
    super(message);
    this.name = 'QuoteBuilderError';
  }
}

export const handleApiError = (error: unknown): string => {
  if (error instanceof QuoteBuilderError) {
    return error.message;
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  if (typeof error === 'string') {
    return error;
  }
  
  return 'An unexpected error occurred';
};

export const createApiError = (error: unknown, context: string): QuoteBuilderError => {
  const message = handleApiError(error);
  return new QuoteBuilderError(
    `${context}: ${message}`,
    'API_ERROR',
    error instanceof Error ? error : undefined
  );
};
