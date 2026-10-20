import { toHast } from 'minimark/hast'
import type { MinimarkNode } from 'minimark'

export type ContentNode = ReturnType<typeof toHast>['children'][number]

export function contentNodes(body: unknown): ContentNode[] {
  const value = (body as { value?: MinimarkNode[] } | undefined)?.value
  return Array.isArray(value) ? toHast({ type: 'minimark', value }).children : []
}

export function contentText(node: ContentNode): string {
  return node.type === 'text'
    ? node.value ?? ''
    : (node.children ?? []).map(contentText).join('')
}
