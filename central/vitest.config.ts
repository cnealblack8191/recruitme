import {defineConfig} from 'vitest/config';
export default defineConfig({test:{include:['central/*.test.ts'],environment:'node'}});
