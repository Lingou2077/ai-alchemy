import type { UserConfigExport } from '@tarojs/cli'

export default {
  env: {
    //  10.200.87.217
    API_BASE_URL: '"http://192.168.206.1:8000"',
    POSTER_SHARE_LANDING_URL: '"https://example.com/ai-alchemy"',
  },
} satisfies UserConfigExport<'webpack5'>
