import { resolve } from 'node:path'
import { defineCollection, defineContentConfig } from '@nuxt/content'

export default defineContentConfig({
  collections: {
    content: defineCollection({
      type: 'page',
      source: {
        cwd: resolve('src/content'),
        include: '**/*.md',
      },
    }),
  },
})
