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

        let jsonStr = match[1].trim()
        // 清理 JSON 字符串中可能被 LLM 添加的多余内容
        // 有些 LLM 会在 JSON 前后添加说明文字，尝试提取纯 JSON
        const jsonTryList = [jsonStr]
        // 尝试提取 { ... } 或 [ ... ] 部分
        const jsonObjMatch = jsonStr.match(/\{[\s\S]*\}/)
        if (jsonObjMatch) jsonTryList.push(jsonObjMatch[0])

        let parsed = false
        for (const tryStr of jsonTryList) {
          try {
            const chartData = JSON.parse(tryStr)
            // 验证基本结构
            if (chartData && typeof chartData === 'object') {
              segments.push({
                type: 'chart',
                data: chartData
              })
              parsed = true
              break
            }
          } catch (e) {
            // 继续尝试下一个候选
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
