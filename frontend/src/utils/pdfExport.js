/**
 * PDF 导出工具
 * 将单条 AI 回复消息导出为 PDF 文件
 *
 * 采用 html2canvas 截图 → jsPDF 嵌入图片的方案，
 * 利用浏览器原生字体渲染，完美支持中文。
 */
import { jsPDF } from 'jspdf'
import html2canvas from 'html2canvas'

/**
 * 导出单条 AI 回复消息为 PDF
 * @param {Object} message - 单条消息 {type, content, reasoning_content, time}
 * @param {string} title - 会话标题（用于文件名）
 */
export async function exportMessageToPDF(message, title = 'AI 回复') {
  if (!message) {
    alert('没有可导出的内容')
    return
  }

  const htmlContent = buildSingleMessageHTML(message, title)

  // 创建全屏遮罩 + 可见容器，让浏览器原生渲染内容
  const overlay = document.createElement('div')
  overlay.style.cssText =
    'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:99999;' +
    'background:rgba(0,0,0,0.5);display:flex;align-items:flex-start;' +
    'justify-content:center;overflow-y:auto;padding:40px 20px;'

  const container = document.createElement('div')
  container.id = '__pdf_export_container__'
  container.style.cssText =
    'width:720px;max-width:100%;background:#ffffff;color:#1e293b;' +
    'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Microsoft YaHei","Helvetica Neue",Arial,sans-serif;' +
    'font-size:14px;line-height:1.7;padding:30px;box-sizing:border-box;border-radius:8px;' +
    'box-shadow:0 4px 24px rgba(0,0,0,0.3);'
  container.innerHTML = htmlContent
  overlay.appendChild(container)
  document.body.appendChild(overlay)

  try {
    // 用 html2canvas 截图（利用浏览器原生字体渲染，中文正常显示）
    const canvas = await html2canvas(container, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#ffffff',
      logging: false,
      // 关键：不使用 letterRendering，避免字符拆分异常
    })

    const imgData = canvas.toDataURL('image/png')

    // 计算图片在 PDF 中的尺寸（保持比例适配 A4）
    const imgWidth = canvas.width
    const imgHeight = canvas.height
    // A4: 210mm x 297mm，留边距 10mm 每侧，可用 190mm 宽
    const pageWidth = 190 // mm
    const margin = 10     // mm
    const ratio = pageWidth / (imgWidth / (canvas.width / imgWidth))  // scale 已包含
    // scale=2 时，实际像素是视觉尺寸的 2 倍
    const pdfImgWidth = pageWidth
    const pdfImgHeight = (imgHeight * pdfImgWidth) / imgWidth

    const pdf = new jsPDF('p', 'mm', 'a4')
    const pageHeight = 297 // mm A4
    let heightLeft = pdfImgHeight
    let position = margin

    // 首页添加图片
    pdf.addImage(imgData, 'PNG', margin, position, pdfImgWidth, pdfImgHeight)
    heightLeft -= (pageHeight - 2 * margin)

    // 内容超出时自动分页
    while (heightLeft > 0) {
      pdf.addPage()
      position = -(pdfImgHeight - heightLeft) + margin
      pdf.addImage(imgData, 'PNG', margin, position, pdfImgWidth, pdfImgHeight)
      heightLeft -= (pageHeight - 2 * margin)
    }

    const safeName = title.replace(/[\\/:*?"<>|]/g, '_').slice(0, 50)
    pdf.save(`${safeName}.pdf`)
  } catch (error) {
    console.error('PDF 导出失败:', error)
    alert('PDF 导出失败，请重试')
  } finally {
    document.body.removeChild(overlay)
  }
}

/**
 * 构建单条消息的导出 HTML
 */
function buildSingleMessageHTML(message, title) {
  const now = new Date().toLocaleString('zh-CN')

  let contentText = ''
  if (typeof message.content === 'string') {
    contentText = message.content
  } else if (Array.isArray(message.content)) {
    contentText = message.content
      .filter(block => block.kind === 'texts' && block.texts)
      .flatMap(block => block.texts)
      .join('\n')
  }

  const formattedContent = formatContentForPDF(contentText)

  let html = `
    <div style="color:#1e293b;">
      <h2 style="font-size:18px;font-weight:700;margin:0 0 4px;color:#0f172a;">${escapeHtml(title)}</h2>
      <p style="font-size:12px;color:#94a3b8;margin:0 0 20px;border-bottom:2px solid #e2e8f0;padding-bottom:12px;">
        导出时间: ${now}
      </p>
  `

  // 推理过程
  if (message.reasoning_content) {
    html += `
      <div style="background:#f8fafc;border-left:3px solid #94a3b8;padding:10px 14px;margin-bottom:14px;border-radius:4px;">
        <div style="font-size:12px;color:#64748b;font-weight:600;margin-bottom:6px;">💭 推理过程</div>
        <pre style="margin:0;font-size:12px;color:#64748b;white-space:pre-wrap;word-wrap:break-word;font-family:'Courier New',Consolas,monospace;line-height:1.5;">${escapeHtml(message.reasoning_content)}</pre>
      </div>
    `
  }

  // 回复内容
  html += `
      <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:16px 18px;">
        <div style="display:flex;align-items:center;margin-bottom:10px;">
          <span style="font-weight:600;font-size:14px;color:#334155;">🤖 AI 回复</span>
          <span style="margin-left:auto;font-size:11px;color:#94a3b8;">${escapeHtml(message.time || '')}</span>
        </div>
        <div style="font-size:14px;line-height:1.8;color:#334155;word-wrap:break-word;white-space:pre-wrap;">${formattedContent}</div>
      </div>

      <p style="font-size:11px;color:#cbd5e1;text-align:center;margin-top:24px;border-top:1px solid #e2e8f0;padding-top:12px;">
        由 AI 聊天助手导出
      </p>
    </div>
  `

  return html
}

/**
 * 格式化内容（简单 Markdown 到 HTML）
 */
function formatContentForPDF(text) {
  if (!text) return ''

  let html = escapeHtml(text)

  // 代码块 ```...```
  html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (match, lang, code) => {
    return `<pre style="background:#1e293b;color:#e2e8f0;padding:12px;border-radius:6px;font-size:12px;font-family:'Courier New',Consolas,monospace;line-height:1.5;overflow-x:auto;white-space:pre-wrap;word-break:break-all;">${escapeHtml(code.trim())}</pre>`
  })

  // 行内代码 `...`
  html = html.replace(/`([^`]+)`/g, '<code style="background:#f1f5f9;color:#e11d48;padding:2px 6px;border-radius:4px;font-size:13px;font-family:\'Courier New\',Consolas,monospace;">$1</code>')

  // 粗体 **...**
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong style="font-weight:700;color:#0f172a;">$1</strong>')

  // 斜体 *...*
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')

  // 标题
  html = html.replace(/^### (.+)$/gm, '<h4 style="font-size:15px;font-weight:700;color:#0f172a;margin:10px 0 6px;">$1</h4>')
  html = html.replace(/^## (.+)$/gm, '<h3 style="font-size:17px;font-weight:700;color:#0f172a;margin:12px 0 6px;">$1</h3>')
  html = html.replace(/^# (.+)$/gm, '<h2 style="font-size:19px;font-weight:700;color:#0f172a;margin:14px 0 6px;">$1</h2>')

  // 无序列表
  html = html.replace(/^- (.+)$/gm, '<li style="margin-left:20px;">$1</li>')

  // 有序列表
  html = html.replace(/^\d+\. (.+)$/gm, '<li style="margin-left:20px;">$1</li>')

  return html
}

/**
 * HTML 转义
 */
function escapeHtml(text) {
  if (!text) return ''
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  }
  return String(text).replace(/[&<>"']/g, c => map[c])
}
