import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'node:path';
export default defineConfig({
  root:path.resolve('central/client'), plugins:[react(),tailwindcss()],
  resolve:{alias:{'@':path.resolve('client/src'),'@shared':path.resolve('shared')}},
  build:{outDir:path.resolve('central-dist/public'),emptyOutDir:true},
  server:{host:'127.0.0.1',port:5177,proxy:{'/api':'http://127.0.0.1:3100'}},
});
