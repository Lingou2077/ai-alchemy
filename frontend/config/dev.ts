import type { UserConfigExport } from '@tarojs/cli'

export default {
  env: {
    API_BASE_URL: '"http://127.0.0.1:8000"',
  },
} satisfies UserConfigExport<'webpack5'>
