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

export class ApiError extends QuoteBuilderError {
  constructor(
    message: string,
    public status: number,
    public details?: string,
    originalError?: Error
  ) {
    super(message, `API_ERROR_${status}`, originalError);
    this.name = 'ApiError';
  }
}

export const handleApiError = (error: unknown): string => {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 400:
        return error.details || 'Invalid request. Please check your input.';
      case 401:
        return 'You need to log in to perform this action.';
      case 403:
        return 'You don\'t have permission to perform this action.';
      case 404:
        return 'The requested resource was not found.';
      case 422:
        return error.details || 'The data you provided is invalid.';
      case 500:
        return 'Server error. Please try again later.';
      default:
        return error.message;
    }
  }
  
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

