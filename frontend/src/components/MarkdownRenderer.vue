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
    }
  },
  computed: {
    renderedContent() {
      let content = this.content
      
      content = content.replace(/\\n/g, '\n')
      content = content.replace(/\\r/g, '')
      
      content = content.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      
      // 处理各种形式的分隔符（---、...、*** 等），统一替换为 <hr>
      content = content.replace(/^[\s]*(\.{3,}|-{3,}|~{3,}|\*{3,})[\s]*$/gm, '\n<hr>\n')
      
      const tableRegex = /(\|.*\|[\r\n]+\|[-:|]+\|[\r\n]+(\|.*\|[\r\n]*)*)/g
      content = content.replace(tableRegex, (match) => {
        return this.parseTable(match)
      })
      
      const md = new MarkdownIt({
        html: true,
        breaks: true,
        linkify: true
      })
      
      return md.render(content)
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
      
      html += '</tbody></table>'
      
      return html
    }
  }
}
</script>

<style>
.markdown-content {
  font-size: 15px;
  line-height: 1.8;
  color: #1a1a1a;
  padding: 10px;
}

.markdown-content h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 20px 0 10px;
  padding-bottom: 8px;
  border-bottom: 2px solid #667eea;
  color: #1a1a1a;
}

.markdown-content h2 {
  font-size: 20px;
  font-weight: 600;
  margin: 18px 0 8px;
  color: #1a1a1a;
}

.markdown-content h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 16px 0 6px;
  color: #1a1a1a;
}

.markdown-content h4 {
  font-size: 16px;
  font-weight: 500;
  margin: 14px 0 6px;
  color: #1a1a1a;
}

.markdown-content p {
  margin: 10px 0;
  color: #1a1a1a;
}

.markdown-content ul,
.markdown-content ol {
  margin: 10px 0;
  padding-left: 24px;
}

.markdown-content li {
  margin: 6px 0;
  color: #1a1a1a;
}

.markdown-content strong {
  font-weight: 600;
  color: #1a1a1a;
}

.markdown-content em {
  font-style: italic;
}

.markdown-content a {
  color: #667eea;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: all 0.2s ease;
}

.markdown-content a:hover {
  border-bottom-color: #667eea;
}

.markdown-content code {
  background-color: #f4f4f4;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 14px;
  font-family: 'Consolas', 'Monaco', monospace;
}

.markdown-content pre {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 10px 0;
  border: 1px solid #e9ecef;
}

.markdown-content pre code {
  background: none;
  padding: 0;
}

.markdown-content blockquote {
  border-left: 4px solid #667eea;
  padding: 10px 15px;
  margin: 10px 0;
  background-color: #f8f9fa;
  border-radius: 0 4px 4px 0;
  color: #555;
}

/* 表格样式 - 增强边框和间距 */
.markdown-content .data-table {
  width: 100%;
  border-collapse: collapse;
  margin: 15px 0;
  font-size: 14px;
  background-color: #ffffff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  /* 添加外边框 */
  border: 2px solid #d0d0d0;
}

.markdown-content .data-table thead {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.markdown-content .data-table thead tr th {
  color: #ffffff !important;
  font-weight: 600;
  padding: 14px 18px;
  text-align: left;
  border: 2px solid #d0d0d0;
  font-size: 14px;
}

.markdown-content .data-table tbody tr {
  border-bottom: 2px solid #d0d0d0;
}

.markdown-content .data-table tbody tr:last-child {
  border-bottom: none;
}

.markdown-content .data-table tbody tr:hover {
  background-color: #f8f9ff;
}

.markdown-content .data-table tbody tr td {
  padding: 14px 18px;
  color: #1a1a1a;
  border: 2px solid #d0d0d0;
  font-size: 14px;
}

.markdown-content .data-table tbody tr td strong {
  color: #1a1a1a;
  font-weight: 600;
}

.markdown-content hr {
  border: none;
  height: 1px;
  background: linear-gradient(90deg, transparent, #c0c0c0, transparent);
  margin: 24px 0;
}
</style>
