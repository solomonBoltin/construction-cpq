/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_CUSTOM_API_DOMAIN?: string;
  // Add more env variables as needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
