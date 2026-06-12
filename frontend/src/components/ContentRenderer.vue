<template>
  <div class="content-renderer">
    <div v-for="(segment, index) in contentSegments" :key="index">
      <MarkdownRenderer v-if="segment.type === 'markdown'" :content="segment.content" :is-streaming="isStreaming" />
      <ChartRenderer v-else-if="segment.type === 'chart'" :chart-data="segment.data" />
      <div v-else-if="segment.type === 'loading'" class="chart-loading">
        📊 图表渲染中...
      </div>
    </div>
  </div>
</template>

<script>
import MarkdownRenderer from './MarkdownRenderer.vue'
import ChartRenderer from './ChartRenderer.vue'

export default {
  name: 'ContentRenderer',
  components: { MarkdownRenderer, ChartRenderer },
  props: {
    // 支持字符串或结构化数组 [{kind: "texts", texts: [...]}, ...]
    content: {
      type: [String, Array],
      required: true
    },
    // 是否正在流式输出中（用于隐藏不完整的图表块）
    isStreaming: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    /**
     * 获取纯文本内容用于渲染
     * 支持字符串和结构化数组两种格式
     */
    plainContent() {
      if (!this.content) return ''
      if (typeof this.content === 'string') return this.content
      if (!Array.isArray(this.content)) return ''
      return this.content
        .filter(block => block.kind === 'texts' && block.texts)
        .flatMap(block => block.texts)
        .join('\n')
    },
    
    contentSegments() {
      const segments = []
      let content = this.plainContent

      if (!content) return segments

      // 移除 tool_calls 原始 XML 标签（防御：正常应由后端 Agent 拦截，
      // 此处在极端情况下兜底，避免 LLM 的工具调用文本泄露到前端展示）
      content = content.replace(/<tool_calls>[\s\S]*?<\/tool_calls>/g, '')
      content = content.replace(/<tool[\s]+call[\s\S]*?<\/tool_call[\s]*>/g, '')
      content = content.replace(/<\/?tool_calls\/?\s*>/g, '')

      // 流式输出中：截断未闭合的结构化块（图表JSON等），避免显示原始数据
      // 等 </chart> 闭合后再整体渲染图表
      if (this.isStreaming) {
        let truncated = false

        // 检测1：未闭合的 <chart> 标签
        const openIdx = content.lastIndexOf('<chart>')
        const closeIdx = content.lastIndexOf('</chart>')
        if (openIdx > closeIdx && openIdx !== -1) {
          content = content.slice(0, openIdx)
          truncated = true
        }

        // 检测2：末尾有未闭合的 JSON 对象/数组（LLM 正在输出图表数据）
        // 匹配以 { 或 [ 或 ' 开头且未闭合的数据块
        if (!truncated) {
          const lastLine = content.split('\n').pop().trim()
          // 常见模式：['chart' / {"chart" / {'chart' / [ / { 开头
          if (/^(\[|[\{'].*(?:chartType|chart_type|"chart)|\{$)/.test(lastLine)) {
            // 回溯到包含该起始标记的行首
            const jsonStart = content.lastIndexOf(lastLine)
            if (jsonStart > 0) {
              // 确保不是在一行的中间（至少前面有换行或内容开头）
              const before = content.slice(0, jsonStart)
              if (before.endsWith('\n') || before === '') {
                content = content.slice(0, jsonStart).trimEnd()
                truncated = true
              }
            }
          }
        }

        // 检测3：末尾有 ``` 代码块但未关闭
        if (!truncated) {
          const codeBlockCount = (content.match(/```/g) || []).length
          if (codeBlockCount % 2 === 1) {
            // 奇数个 ``` → 有未闭合代码块
            const lastCode = content.lastIndexOf('```')
            content = content.slice(0, lastCode).trimEnd()
            truncated = true
          }
        }

        if (truncated) {
          segments.push({ type: 'markdown', content: content.trimEnd() })
          segments.push({ type: 'loading' })
          return segments
        }
      }

      // HTML 实体解码（多层解码，处理 LLM 可能的重复转义）
      for (let i = 0; i < 3; i++) {
        content = content.replace(/&lt;chart&gt;/g, '<chart>')
        content = content.replace(/&lt;\/chart&gt;/g, '</chart>')
        content = content.replace(/&quot;/g, '"')
        content = content.replace(/&amp;/g, '&')
        content = content.replace(/&#39;/g, "'")
        // 处理 Unicode 转义的尖括号
        content = content.replace(/\\u003c/gi, '<').replace(/\\u003e/gi, '>')
        // 处理反斜杠转义的尖括号（LLM 有时会输出 \<chart\>）
        content = content.replace(/\\<chart\\>/g, '<chart>').replace(/\\<\/chart\\>/g, '</chart>')
      }

      // 移除可能包裹在 <chart> 标签外的 markdown 代码块标记
      // 匹配 `...<chart>...</chart>` 或 ``` ... <chart>...</chart> ... ```
      content = content.replace(
        /`{1,3}([\s\S]*?)<chart>([\s\S]*?)<\/chart>([\s\S]*?)`{1,3}/g,
        '<chart>$2</chart>'
      )

      const chartRegex = /<chart>([\s\S]*?)<\/chart>/g

      let lastIndex = 0
      let match

      while ((match = chartRegex.exec(content)) !== null) {
        if (match.index > lastIndex) {
          segments.push({
            type: 'markdown',
            content: content.slice(lastIndex, match.index)
          })
        }

        let rawJson = match[1].trim()

        // 构建多级解码候选列表，按优先级排列
        const candidates = []

        // 候选0：原始内容
        candidates.push(rawJson)

        // 候选1：单层反斜杠转义引号 \" → "
        let s1 = rawJson.replace(/\\"/g, '"')
        candidates.push(s1)

        // 候选2：双层反斜杠转义 \\\" → "
        let s2 = rawJson.replace(/\\\\\"/g, '"').replace(/\\"/g, '"')
        candidates.push(s2)

        // 候选3：去掉所有反斜杠后尝试（极端回退）
        let s3 = rawJson.replace(/\\/g, '')
        candidates.push(s3)

        // 对每个候选都尝试：整体解析 + 正则提取子 JSON 解析
        const allTries = []
        for (const c of candidates) {
          allTries.push(c)
          const sub = c.match(/\{[\s\S]*\}/)
          if (sub) allTries.push(sub[0])
        }

        let parsed = false
        for (const tryStr of allTries) {
          try {
            const chartData = JSON.parse(tryStr)
            // 验证基本结构
            if (chartData && typeof chartData === 'object' && chartData.chartType) {
              segments.push({
                type: 'chart',
                data: chartData
              })
              parsed = true
              break
            }
          } catch (e) {
            // 继续下一个候选
          }
        }

        if (!parsed) {
          // JSON 解析全部失败，作为 markdown 回退显示原始文本
          segments.push({
            type: 'markdown',
            content: match[0]
          })
        }

        lastIndex = chartRegex.lastIndex
      }

      if (lastIndex < content.length) {
        segments.push({
          type: 'markdown',
          content: content.slice(lastIndex)
        })
      }

      return segments
    }
  }
}
</script>

<style scoped>
.content-renderer {
  width: 100%;
}

.chart-loading {
  padding: 16px 20px;
  margin: 10px 0;
  background: var(--app-bg-secondary);
  border: 1px dashed var(--card-border);
  border-radius: 8px;
  color: var(--text-muted);
  font-size: 14px;
  text-align: center;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}
</style>
