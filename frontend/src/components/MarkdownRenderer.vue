<template>
  <div class="markdown-content" v-html="renderedContent"></div>
</template>

<script>
import MarkdownIt from 'markdown-it'

export default {
  name: 'MarkdownRenderer',
  props: {
    content: {
      type: String,
      required: true
    },
    // 是否正在流式输出中（用于提前渲染不完整表格）
    isStreaming: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    renderedContent() {
      let content = this.content
      
      content = content.replace(/\\n/g, '\n')
      content = content.replace(/\\r/g, '')
      
      content = content.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      
      // 处理各种形式的分隔符（---、...、*** 等），统一替换为 markdown 分隔线
      // 使用 --- 而非 <hr>，避免开启 HTML 块吞没后续标题
      content = content.replace(/^[\s]*(\.{3,}|-{3,}|~{3,}|\*{3,})[\s]*$/gm, '\n\n---\n\n')
      
      // 流式输出中：检测仅有表头行的不完整表格，补全分隔符使其提前渲染
      if (this.isStreaming) {
        content = content.replace(
          /(?:^|\n)(\|[^\n|]+\|)[\r\n]*$/,
          (match, headerRow) => {
            const colCount = (headerRow.match(/\|/g) || []).length - 1
            const sep = '|' + Array(Math.max(1, colCount)).fill('---').join('|') + '|'
            return match.trimEnd() + '\n' + sep + '\n'
          }
        )
      }

      // 用 HTML 注释占位符标记表格位置，先替换为 HTML 表格
      // markdown-it (html:true) 会原样保留 HTML 注释，不会被转义
      const tableParts = []
      const tableRegex = /(\|.*\|[\r\n]+\|[-:|]+\|[\r\n]+(\|.*\|[\r\n]*)*)/g
      content = content.replace(tableRegex, (match) => {
        const idx = tableParts.length
        tableParts.push(this.parseTable(match))
        return `<!--TABLE_PLACEHOLDER_${idx}-->`
      })

      // 清理表格占位符紧邻的多余分隔线 --- / ***
      // LLM 常在章节和表格间用 --- 分隔，渲染后会变成多余的 <hr>
      content = content.replace(
        /\n{0,2}([\s]*(?:-{3,}|\.{3,}|~{3,}|\*{3,})[\s]*)\n*(<!--TABLE_PLACEHOLDER_\d+-->)/g,
        '$2'
      )
      // 也清理表格后的多余分隔线
      content = content.replace(
        /(<!--TABLE_PLACEHOLDER_\d+-->)\n*([\s]*(?:-{3,}|\.{3,}|~{3,}|\*{3,})[\s]*)\n{0,2}/g,
        '$1\n'
      )

      const md = new MarkdownIt({
        html: true,
        breaks: true,
        linkify: true
      })
      
      // 对非表格部分做 markdown 渲染，然后还原表格 HTML
      let result = md.render(content)
      
      // 最终清理：移除表格 HTML 紧邻的 <hr> 标签（markdown-it 可能已将残余 --- 渲染为 hr）
      for (let i = 0; i < tableParts.length; i++) {
        result = result.replace(`<!--TABLE_PLACEHOLDER_${i}-->`, tableParts[i])
      }
      result = result.replace(
        /<hr[^>]*>\s*(<table class="data-table">)/g,
        '$1'
      )
      result = result.replace(
        /(<\/table>\s*)\s*<hr[^>]*>/g,
        '$1'
      )
      
      return result
    }
  },
  methods: {
    parseTable(tableText) {
      const lines = tableText.split('\n').filter(line => line.trim() && line.includes('|'))
      
      if (lines.length < 2) {
        return tableText
      }
      
      let html = '<table class="data-table"><thead><tr>'
      
      const headerParts = lines[0].split('|').filter(p => p.trim() !== '')
      headerParts.forEach(part => {
        const cleaned = part.trim().replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        html += `<th>${cleaned}</th>`
      })
      html += '</tr></thead><tbody>'
      
      for (let i = 2; i < lines.length; i++) {
        const line = lines[i].trim()
        if (!line || !line.includes('|')) continue
        if (line.match(/^\|[-:|]+\|$/)) continue
        
        html += '<tr>'
        const parts = line.split('|').filter(p => p.trim() !== '')
        parts.forEach(part => {
          const cleaned = part.trim().replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
          html += `<td>${cleaned}</td>`
        })
        html += '</tr>'
      }
      
      html += '</tbody></table>\n\n'

      return html
    }
  }
}
</script>

<style>
.markdown-content {
  font-size: 15px;
  line-height: 1.8;
  color: #e2e8f0;
  padding: 10px;
}

.markdown-content h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 20px 0 10px;
  padding-bottom: 8px;
  border-bottom: 2px solid #667eea;
  color: #f1f5f9;
}

.markdown-content h2 {
  font-size: 20px;
  font-weight: 600;
  margin: 18px 0 8px;
  color: #f1f5f9;
}

.markdown-content h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 16px 0 6px;
  color: #f1f5f9;
}

.markdown-content h4 {
  font-size: 16px;
  font-weight: 500;
  margin: 14px 0 6px;
  color: #f1f5f9;
}

.markdown-content p {
  margin: 10px 0;
  color: #e2e8f0;
}

.markdown-content ul,
.markdown-content ol {
  margin: 10px 0;
  padding-left: 24px;
}

.markdown-content li {
  margin: 6px 0;
  color: #e2e8f0;
}

.markdown-content strong {
  font-weight: 600;
  color: #f1f5f9;
}

.markdown-content em {
  font-style: italic;
  color: #cbd5e1;
}

.markdown-content a {
  color: #93c5fd;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: all 0.2s ease;
}

.markdown-content a:hover {
  border-bottom-color: #93c5fd;
}

.markdown-content code {
  background-color: #1e293b;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 14px;
  font-family: 'Consolas', 'Monaco', monospace;
  color: #fbbf24;
}

.markdown-content pre {
  background-color: #0f172a;
  padding: 15px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 10px 0;
  border: 1px solid #334155;
}

.markdown-content pre code {
  background: none;
  padding: 0;
  color: #e2e8f0;
}

.markdown-content blockquote {
  border-left: 4px solid #667eea;
  padding: 10px 15px;
  margin: 10px 0;
  background-color: #1e293b;
  border-radius: 0 4px 4px 0;
  color: #94a3b8;
}

/* 表格样式 - 增强边框和间距 */
.markdown-content .data-table {
  width: 100%;
  border-collapse: collapse;
  margin: 15px 0;
  font-size: 14px;
  background-color: #1e293b;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
  /* 添加外边框 */
  border: 2px solid #475569;
}

.markdown-content .data-table thead {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.markdown-content .data-table thead tr th {
  color: #ffffff !important;
  font-weight: 600;
  padding: 14px 18px;
  text-align: left;
  border: 2px solid #475569;
  font-size: 14px;
}

.markdown-content .data-table tbody tr {
  border-bottom: 2px solid #334155;
}

.markdown-content .data-table tbody tr:last-child {
  border-bottom: none;
}

.markdown-content .data-table tbody tr:hover {
  background-color: #1a2332;
}

.markdown-content .data-table tbody tr td {
  padding: 14px 18px;
  color: #e2e8f0;
  border: 2px solid #334155;
  font-size: 14px;
}

.markdown-content .data-table tbody tr td strong {
  color: #f1f5f9;
  font-weight: 600;
}

.markdown-content hr {
  border: none;
  height: 1px;
  background: linear-gradient(90deg, transparent, #c0c0c0, transparent);
  margin: 24px 0;
}
</style>
