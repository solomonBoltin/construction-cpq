import path from 'path';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    console.log('Loaded environment into frontend run')
    
    return {
      define: {
        'process.env.SOME_ENV_VAR': JSON.stringify(env.SOME_ENV_VAR || 'default_value'),
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '.'),
        }
      },
      server: {
        proxy: {
          '/api': {
            target: 'http://localhost:8000',
            changeOrigin: true,
          },
        },
      },
    };
});
