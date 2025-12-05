/// <reference types="vite/client" />

/**
 * Type definitions for Vite environment variables.
 * This file provides TypeScript support for import.meta.env in Vite projects.
 * 
 * Add additional VITE_* environment variables here as they are used in the application.
 * See .env.example and README.md for available configuration options.
 */

interface ImportMetaEnv {
  /** Custom API domain for backend connectivity. Defaults to empty string (same domain). */
  readonly VITE_CUSTOM_API_DOMAIN?: string;
  // Add more VITE_* environment variables here as needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
