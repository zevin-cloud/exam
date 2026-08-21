<template>
  <div class="essay-editor" @dragover.prevent @drop.prevent="handleDrop">
    <div class="editor-toolbar">
      <div class="tool-group" aria-label="Markdown 快捷工具">
        <button type="button" class="tool-button is-strong" title="加粗" @click="wrapSelection('**', '**', '重点内容')">B</button>
        <button type="button" class="tool-button is-italic" title="斜体" @click="wrapSelection('*', '*', '强调内容')">I</button>
        <button type="button" class="tool-button" title="无序列表" @click="prefixLines('- ')">• 列表</button>
        <button type="button" class="tool-button tool-code" title="行内代码" @click="wrapSelection('`', '`', '代码')">&lt;/&gt;</button>
        <button type="button" class="tool-button image-button" :disabled="uploading" @click="chooseImages">
          <ImagePlus :size="15" /> {{ uploading ? '上传中' : '插入图片' }}
        </button>
      </div>
      <div class="mode-switch" role="tablist" aria-label="编辑模式">
        <button type="button" :class="{ active: mode === 'edit' }" @click="mode = 'edit'">编辑</button>
        <button type="button" :class="{ active: mode === 'preview' }" @click="mode = 'preview'">预览</button>
      </div>
    </div>

    <div v-show="mode === 'edit'" class="writing-surface">
      <a-textarea
        ref="editorRef"
        v-model="localContent"
        :autosize="{ minRows: 7, maxRows: 18 }"
        placeholder="请输入答案。支持 Markdown，也可以粘贴、拖入或选择图片…"
        @input="emitAnswer"
        @paste="handlePaste"
      />
      <div class="writing-hint">支持 Markdown · 图片可直接粘贴/拖入 · 单张不超过 5 MB</div>
    </div>

    <div v-show="mode === 'preview'" class="preview-surface">
      <MarkdownAnswer :answer="currentAnswer" empty-text="输入内容后可在这里查看最终卷面效果" />
    </div>

    <div v-if="localAttachments.length" class="attachment-strip">
      <span class="attachment-label">本题图片</span>
      <div v-for="item in localAttachments" :key="item.id" class="attachment-chip">
        <ImageIcon :size="14" />
        <span :title="item.name">{{ item.name }}</span>
        <button type="button" title="删除图片" @click="removeAttachment(item)"><X :size="13" /></button>
      </div>
    </div>

    <input ref="fileInput" class="visually-hidden" type="file" accept="image/jpeg,image/png,image/webp" multiple @change="handleFileInput" />
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { Message } from '@arco-design/web-vue'
import { Image as ImageIcon, ImagePlus, X } from 'lucide-vue-next'
import { examApi } from '@/api'
import MarkdownAnswer from './MarkdownAnswer.vue'

const props = defineProps({
  modelValue: { type: [String, Object], default: '' },
  recordId: { type: [String, Number], required: true },
  questionId: { type: [String, Number], required: true }
})
const emit = defineEmits(['update:modelValue', 'change'])

const editorRef = ref(null)
const fileInput = ref(null)
const mode = ref('edit')
const uploading = ref(false)
const localContent = ref('')
const localAttachments = ref([])
let syncingFromParent = false

watch(() => props.modelValue, value => {
  syncingFromParent = true
  if (typeof value === 'string') {
    localContent.value = value
    localAttachments.value = []
  } else {
    localContent.value = String(value?.content || '')
    localAttachments.value = Array.isArray(value?.attachments) ? [...value.attachments] : []
  }
  nextTick(() => { syncingFromParent = false })
}, { deep: true, immediate: true })

const currentAnswer = computed(() => ({
  format: 'markdown',
  content: localContent.value,
  attachments: localAttachments.value
}))

const emitAnswer = () => {
  if (syncingFromParent) return
  emit('update:modelValue', currentAnswer.value)
  emit('change')
}

const textarea = () => editorRef.value?.$el?.querySelector('textarea') || editorRef.value?.textarea

const replaceSelection = async (replacement, selectionStart) => {
  localContent.value = replacement
  emitAnswer()
  await nextTick()
  const input = textarea()
  if (input) {
    input.focus()
    const cursor = selectionStart ?? replacement.length
    input.setSelectionRange(cursor, cursor)
  }
}

const wrapSelection = (before, after, fallback) => {
  const input = textarea()
  const start = input?.selectionStart ?? localContent.value.length
  const end = input?.selectionEnd ?? start
  const selected = localContent.value.slice(start, end) || fallback
  const nextValue = `${localContent.value.slice(0, start)}${before}${selected}${after}${localContent.value.slice(end)}`
  replaceSelection(nextValue, start + before.length + selected.length)
}

const prefixLines = (prefix) => {
  const input = textarea()
  const start = input?.selectionStart ?? localContent.value.length
  const end = input?.selectionEnd ?? start
  const selected = localContent.value.slice(start, end) || '列表项'
  const replacement = selected.split('\n').map(line => `${prefix}${line}`).join('\n')
  replaceSelection(`${localContent.value.slice(0, start)}${replacement}${localContent.value.slice(end)}`, start + replacement.length)
}

const chooseImages = () => fileInput.value?.click()

const appendImageMarker = (attachment) => {
  const safeName = String(attachment.name || '答题图片').replace(/[\[\]()]/g, '')
  const marker = `![${safeName}](attachment:${attachment.id})`
  localContent.value = `${localContent.value}${localContent.value.trim() ? '\n\n' : ''}${marker}`
  localAttachments.value.push(attachment)
  emitAnswer()
}

const uploadFiles = async (files) => {
  const images = [...files].filter(file => file.type.startsWith('image/'))
  if (!images.length) return
  if (localAttachments.value.length + images.length > 6) {
    Message.warning('每道题最多上传 6 张图片')
    return
  }
  uploading.value = true
  try {
    for (const file of images) {
      if (file.size > 5 * 1024 * 1024) {
        Message.warning(`${file.name} 超过 5 MB，已跳过`)
        continue
      }
      const formData = new FormData()
      formData.append('file', file)
      const attachment = await examApi.uploadAttachment(props.recordId, props.questionId, formData)
      appendImageMarker(attachment)
    }
  } catch {
    // 统一请求层已经提示具体错误，并保留此前已成功上传的图片。
  } finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

const handleFileInput = (event) => uploadFiles(event.target.files || [])
const handleDrop = (event) => uploadFiles(event.dataTransfer?.files || [])
const handlePaste = (event) => {
  const files = [...(event.clipboardData?.files || [])].filter(file => file.type.startsWith('image/'))
  if (files.length) {
    event.preventDefault()
    uploadFiles(files)
  }
}

const removeAttachment = async (attachment) => {
  try {
    await examApi.deleteAttachment(attachment.id)
    localAttachments.value = localAttachments.value.filter(item => item.id !== attachment.id)
    const escapedId = String(attachment.id).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const markerPattern = new RegExp(`!?\\[[^\\]]*\\]\\(attachment:${escapedId}\\)\\s*`, 'g')
    localContent.value = localContent.value.replace(markerPattern, '').trim()
    emitAnswer()
  } catch {
    // 统一请求层已经提示具体错误。
  }
}
</script>

<style scoped>
.essay-editor {
  overflow: hidden;
  border: 1px solid #d8e1ed;
  border-radius: var(--app-radius-panel);
  background: #fff;
  transition: border-color .18s, box-shadow .18s;
}
.essay-editor:focus-within {
  border-color: #78a8f7;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, .1);
}
.editor-toolbar {
  min-height: 42px;
  padding: 5px 7px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-bottom: 1px solid #e7edf5;
  background: #f8fafc;
}
.tool-group { display: flex; align-items: center; gap: 3px; flex-wrap: wrap; }
.tool-button {
  min-height: 30px;
  padding: 0 9px;
  border: 0;
  border-radius: var(--app-radius-control);
  color: #526177;
  background: transparent;
  cursor: pointer;
  font-size: 12px;
}
.tool-button:hover { color: #1f5fca; background: #eaf2ff; }
.tool-button:disabled { opacity: .55; cursor: wait; }
.tool-button.is-strong { font-weight: 800; }
.tool-button.is-italic { font-family: Georgia, serif; font-style: italic; }
.tool-button.tool-code { font-family: Consolas, monospace; }
.tool-button.image-button { display: inline-flex; align-items: center; gap: 5px; color: #2563eb; }
.mode-switch {
  flex: 0 0 auto;
  display: flex;
  padding: 2px;
  border: 1px solid #dce4ef;
  border-radius: var(--app-radius-control);
  background: #fff;
}
.mode-switch button {
  padding: 4px 11px;
  border: 0;
  border-radius: var(--app-radius-control);
  color: #718096;
  background: transparent;
  cursor: pointer;
  font-size: 12px;
}
.mode-switch button.active { color: #1d4ed8; background: #eaf2ff; font-weight: 650; }
.writing-surface { background: var(--color-bg-2); }
.writing-surface :deep(.arco-textarea) {
  padding: 16px 18px 8px;
  border: 0;
  box-shadow: none;
  resize: vertical;
  color: #1f2c3d;
  background: transparent;
  line-height: 1.8;
}
.writing-surface :deep(.arco-textarea:focus) { box-shadow: none; }
.writing-hint { padding: 4px 18px 10px; color: #98a4b3; font-size: 11px; }
.preview-surface { min-height: 192px; padding: 17px 19px; background: #fff; }
.attachment-strip {
  padding: 8px 10px;
  display: flex;
  align-items: center;
  gap: 7px;
  flex-wrap: wrap;
  border-top: 1px solid #edf1f6;
  background: #fbfcfe;
}
.attachment-label { color: #8491a4; font-size: 11px; }
.attachment-chip {
  max-width: 230px;
  padding: 5px 6px 5px 8px;
  display: flex;
  align-items: center;
  gap: 5px;
  border: 1px solid #d9e5f7;
  border-radius: var(--app-radius-control);
  color: #376095;
  background: #f2f7ff;
  font-size: 11px;
}
.attachment-chip span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.attachment-chip button { display: flex; padding: 2px; border: 0; color: #7991af; background: transparent; cursor: pointer; }
.attachment-chip button:hover { color: #dc2626; }
.visually-hidden { position: absolute; width: 1px; height: 1px; overflow: hidden; opacity: 0; pointer-events: none; }
@media (max-width: 680px) {
  .editor-toolbar { align-items: flex-start; }
  .tool-button { padding: 0 6px; }
}
</style>
