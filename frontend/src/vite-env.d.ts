/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API?: string;
  readonly VITE_VITIMA_URL?: string;
}
interface ImportMeta {
  readonly env: ImportMetaEnv;
}
