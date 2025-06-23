
import { USE_MOCK_API } from '../constants';
import { quoteProcessMockApi } from './quoteProcessMockClient';
import { quoteProcessClient } from './quoteProcessClient';

// This is a simplified union for the functions we are using from mock/real client
// A more robust solution would be an interface that both clients implement.
export const apiClient = USE_MOCK_API ? quoteProcessMockApi : quoteProcessClient;
