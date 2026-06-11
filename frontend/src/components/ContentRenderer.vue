<template>
  <div class="content-renderer">
    <div v-for="(segment, index) in contentSegments" :key="index">
      <MarkdownRenderer v-if="segment.type === 'markdown'" :content="segment.content" />
      <ChartRenderer v-else-if="segment.type === 'chart'" :chart-data="segment.data" />
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
    content: {
      type: String,
      required: true
    }
  },
  computed: {
    contentSegments() {
      const segments = []
      let content = this.content

      if (!content) return segments

      // 移除 tool_calls 原始 XML 标签（防御：正常应由后端 Agent 拦截，
      // 此处在极端情况下兜底，避免 LLM 的工具调用文本泄露到前端展示）
      content = content.replace(/<tool_calls>[\s\S]*?<\/tool_calls>/g, '')
      content = content.replace(/<tool[\s]+call[\s\S]*?<\/tool_call[\s]*>/g, '')
      content = content.replace(/<\/?tool_calls\/?\s*>/g, '')

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
</style>
