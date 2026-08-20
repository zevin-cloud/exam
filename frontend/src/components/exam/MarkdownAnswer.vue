<template>
  <div class="markdown-answer" :class="{ 'is-empty': !hasAnswer }">
    <div v-if="hasAnswer" ref="contentRef" class="markdown-body" v-html="renderedHtml" @click="handleContentClick"></div>
    <span v-else class="empty-answer">{{ emptyText }}</span>
    <el-image-viewer v-if="previewUrl" :url-list="[previewUrl]" hide-on-click-modal @close="previewUrl = ''" />
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'
import { examApi } from '@/api'

const props = defineProps({
  answer: { type: [String, Object, Array], default: '' },
  emptyText: { type: String, default: '（未作答）' }
})

const contentRef = ref(null)
const previewUrl = ref('')
const objectUrls = new Map()

const normalizedAnswer = computed(() => {
  if (typeof props.answer === 'string') return { content: props.answer, attachments: [] }
  if (props.answer && typeof props.answer === 'object' && !Array.isArray(props.answer)) {
    return {
      content: String(props.answer.content || ''),
      attachments: Array.isArray(props.answer.attachments) ? props.answer.attachments : []
    }
  }
  if (Array.isArray(props.answer)) return { content: props.answer.join('、'), attachments: [] }
  return { content: '', attachments: [] }
})

const hasAnswer = computed(() => Boolean(
  normalizedAnswer.value.content.trim() || normalizedAnswer.value.attachments.length
))

const markdown = new MarkdownIt({ html: false, linkify: true, breaks: true })
const defaultImageRenderer = markdown.renderer.rules.image
markdown.renderer.rules.image = (tokens, index, options, env, self) => {
  const source = tokens[index].attrGet('src') || ''
  try {
    const parsed = new URL(source)
    if (parsed.hostname !== 'exam-attachment.local') {
      return '<span class="blocked-image">［外部图片已阻止］</span>'
    }
  } catch {
    return '<span class="blocked-image">［无效图片］</span>'
  }
  return defaultImageRenderer
    ? defaultImageRenderer(tokens, index, options, env, self)
    : self.renderToken(tokens, index, options)
}

const renderedHtml = computed(() => {
  const answer = normalizedAnswer.value
  const referencedIds = new Set(
    [...answer.content.matchAll(/attachment:(\d+)/g)].map(match => Number(match[1]))
  )
  const unreferencedImages = answer.attachments
    .filter(item => item?.id && !referencedIds.has(Number(item.id)))
    .map(item => `![${item.name || '答题图片'}](attachment:${item.id})`)
    .join('\n\n')
  const source = [answer.content, unreferencedImages].filter(Boolean).join('\n\n')
  const attachmentSource = source.replace(
    /attachment:(\d+)/g,
    'https://exam-attachment.local/$1'
  )
  return DOMPurify.sanitize(markdown.render(attachmentSource), {
    USE_PROFILES: { html: true }
  })
})

const releaseObjectUrls = () => {
  objectUrls.forEach(url => URL.revokeObjectURL(url))
  objectUrls.clear()
}

const hydrateProtectedImages = async () => {
  await nextTick()
  const images = [...(contentRef.value?.querySelectorAll('img') || [])]
  const pending = images.map(async image => {
    let parsed
    try {
      parsed = new URL(image.getAttribute('src'), window.location.origin)
    } catch {
      image.remove()
      return
    }
    if (parsed.hostname !== 'exam-attachment.local') {
      image.remove()
      return
    }
    const attachmentId = Number(parsed.pathname.replace('/', ''))
    if (!Number.isInteger(attachmentId)) {
      image.remove()
      return
    }
    image.classList.add('protected-answer-image')
    image.dataset.attachmentId = String(attachmentId)
    try {
      let objectUrl = objectUrls.get(attachmentId)
      if (!objectUrl) {
        const blob = await examApi.getAttachment(attachmentId)
        objectUrl = URL.createObjectURL(blob)
        objectUrls.set(attachmentId, objectUrl)
      }
      image.src = objectUrl
      image.title = '点击查看大图'
    } catch {
      image.replaceWith(document.createTextNode('［图片加载失败］'))
    }
  })
  await Promise.all(pending)
}

const handleContentClick = (event) => {
  const image = event.target.closest?.('img.protected-answer-image')
  if (image?.src) previewUrl.value = image.src
}

watch(renderedHtml, () => {
  releaseObjectUrls()
  hydrateProtectedImages()
}, { immediate: true })

onBeforeUnmount(releaseObjectUrls)
</script>

<style scoped>
.markdown-answer {
  color: #26354a;
  line-height: 1.75;
  overflow-wrap: anywhere;
}

.empty-answer {
  color: #9aa6b6;
  font-style: italic;
}

.markdown-body :deep(p) { margin: 0 0 10px; }
.markdown-body :deep(p:last-child) { margin-bottom: 0; }
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  color: #172033;
  line-height: 1.35;
  margin: 18px 0 8px;
}
.markdown-body :deep(h1) { font-size: 20px; }
.markdown-body :deep(h2) { font-size: 18px; }
.markdown-body :deep(h3) { font-size: 16px; }
.markdown-body :deep(ul),
.markdown-body :deep(ol) { padding-left: 24px; margin: 8px 0; }
.markdown-body :deep(blockquote) {
  margin: 10px 0;
  padding: 8px 14px;
  color: #52647e;
  background: #f4f7fb;
  border-left: 3px solid #79a8f7;
}
.markdown-body :deep(code) {
  padding: 2px 5px;
  border-radius: 4px;
  color: #b4235a;
  background: #f5f0f3;
  font-family: Consolas, 'SFMono-Regular', monospace;
  font-size: 0.9em;
}
.markdown-body :deep(pre) {
  padding: 14px;
  overflow: auto;
  border-radius: 8px;
  color: #dce7f7;
  background: #182335;
}
.markdown-body :deep(pre code) { padding: 0; color: inherit; background: transparent; }
.markdown-body :deep(a) { color: #2563eb; }
.markdown-body :deep(.blocked-image) { color: #a16207; font-size: 12px; }
.markdown-body :deep(img.protected-answer-image) {
  display: block;
  max-width: min(100%, 720px);
  max-height: 520px;
  margin: 14px 0;
  border: 1px solid #d8e0eb;
  border-radius: 10px;
  box-shadow: 0 6px 20px rgba(24, 35, 53, 0.08);
  cursor: zoom-in;
  object-fit: contain;
}
</style>
