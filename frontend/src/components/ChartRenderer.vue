<template>
  <div class="chart-container">
    <h4 class="chart-title">{{ title }}</h4>
    <!-- 柱状图 / 折线图 -->
    <div v-if="type === 'bar' || type === 'line'" class="css-chart">
      <div class="css-bars">
        <div v-for="(item, idx) in barItems" :key="idx" class="css-bar-row">
          <span class="css-label" :title="item.label">{{ item.label }}</span>
          <div class="css-track">
            <div class="css-fill" :style="{ width: item.pct + '%', background: item.gradient }">
              <span class="css-value">{{ formatValue(item.value) }}{{ item.suffix || '' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 饼图：SVG 统一坐标系 -->
    <div v-else-if="type === 'pie'" class="pie-wrapper">
      <svg :viewBox="`0 0 ${svgW} ${svgH}`" class="pie-svg">
        <!-- 饼图圆（conic-gradient 通过 foreignObject 嵌入） -->
        <foreignObject :x="cx - R" :y="cy - R" width="140" height="140">
          <div class="pie-circle" :style="{ background: pieConicGradient }"></div>
        </foreignObject>

        <!-- 各扇区引导线 + 标签 -->
        <template v-for="(lbl, idx) in pieLabels" :key="'seg-'+idx">
          <!-- 引导线 -->
          <polyline
            :points="lbl.polyPoints"
            fill="none"
            :stroke="PIE_COLORS[idx % PIE_COLORS.length]"
            stroke-width="1.3"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <!-- 端点圆点 -->
          <circle
            :cx="lbl.endX" :cy="lbl.endY" r="2.8"
            :fill="PIE_COLORS[idx % PIE_COLORS.length]"
          />
          <!-- 标签文字 -->
          <text
            :x="lbl.textX" :y="lbl.textY"
            :text-anchor="lbl.anchor"
            dominant-baseline="central"
            class="pie-label-txt"
          >{{ lbl.name }}</text>
          <!-- 百分比 -->
          <text
            :x="lbl.pctX" :y="lbl.pctY"
            :text-anchor="lbl.anchor"
            dominant-baseline="central"
            class="pie-label-pct"
          >{{ lbl.pct }}</text>
        </template>
      </svg>

      <!-- 底部图例 -->
      <div class="pie-legend-grid">
        <div v-for="(item, idx) in pieItems" :key="'leg-' + idx" class="legend-cell">
          <span class="legend-dot" :style="{ background: PIE_COLORS[idx % PIE_COLORS.length] }"></span>
          <span class="legend-name" :title="item.label">{{ item.label }}</span>
          <span class="legend-pct">{{ Number(item.pct).toFixed(1) }}%</span>
        </div>
      </div>
    </div>

    <div v-else class="chart-fallback">不支持的图表类型: {{ type }}</div>
  </div>
</template>

<script>
const PIE_COLORS = ['#667eea','#11998e','#fc4a1a','#ee0979','#4facfe','#43e97b','#fa709a','#f093fb']
const COLOR_PAIRS = [
  ['#667eea','#764ba2'],['#11998e','#38ef7d'],['#fc4a1a','#f7b733'],
  ['#ee0979','#ff6a00'],['#4facfe','#00f2fe'],['#43e97b','#38f9d7'],
  ['#fa709a','#fee140'],['#a18cd1','#fbc2eb']
]
const DEG = Math.PI / 180

export default {
  name: 'ChartRenderer',
  props: { chartData: { type: Object, required: true } },
  data() { return { PIE_COLORS } },
  computed: {
    cd() { return this.chartData || {} },
    title() { return this.cd.title || '' },
    type() { return (this.cd.chartType || 'bar').toLowerCase() },
    labels() { return this.cd.labels || [] },
    rawDatasets() { return this.cd.datasets || [] },

    /* SVG 画布参数 */
    svgW() { return 260 },
    svgH() { return 240 },
    cx() { return 110 },
    cy() { return 115 },
    R() { return 62 },

    barItems() {
      const allValues = []; let isPercent = false
      for (const ds of this.rawDatasets) {
        if (ds.label && /%|率/.test(String(ds.label))) isPercent = true
        for (const v of (ds.data || [])) allValues.push(Number(v) || 0)
      }
      const maxVal = Math.max(...allValues, 1)
      const suffix = isPercent ? '%' : ''
      const items = []
      for (let i = 0; i < this.labels.length; i++) {
        let value = 0
        for (const ds of this.rawDatasets) {
          if (ds.data && ds.data[i] !== undefined) value = Number(ds.data[i]) || 0
        }
        const pct = Math.max(6, Math.min(100, (value / maxVal) * 100))
        items.push({ label: String(this.labels[i]), value, pct, suffix, gradient: this.getGradient(i) })
      }
      return items
    },

    // ====== 饼图数据 ======
    pieItems() {
      const total = (this.rawDatasets[0]?.data || []).reduce((a, b) => a + (Number(b) || 0), 0)
      return (this.rawDatasets[0]?.data || []).map((v, i) => ({
        label: String(this.labels[i] || ''), value: Number(v) || 0,
        pct: total > 0 ? ((v / total) * 100) : 0
      }))
    },

    /** conic-gradient 字符串 */
    pieConicGradient() {
      if (!this.pieItems.length) return PIE_COLORS[0]
      const stops = []
      let angle = 0
      for (let i = 0; i < this.pieItems.length; i++) {
        const end = angle + this.pieItems[i].pct * 3.6
        stops.push(`${PIE_COLORS[i % PIE_COLORS.length]} ${angle.toFixed(2)}deg ${end.toFixed(2)}deg`)
        angle = end
      }
      return `conic-gradient(${stops.join(', ')})`
    },

    /**
     * 计算每个扇区的引导线+标签位置
     * 所有坐标都在 svgW x svgH 的统一坐标系中
     */
    pieLabels() {
      const cx = this.cx, cy = this.cy, R = this.R
      const labels = []
      let angle = 0 // 扇区起始角度(度)，从12点顺时针

      for (let i = 0; i < this.pieItems.length; i++) {
        const item = this.pieItems[i]
        const spanDeg = item.pct * 3.6
        const midDeg = angle + spanDeg / 2  // 扇区中心角度
        const rad = ((midDeg - 90) * DEG)    // 转标准弧度(0°=3点钟方向)

        const cosA = Math.cos(rad)
        const sinA = Math.sin(rad)

        // --- 引导线三段折点 ---
        // P1: 饼边缘（距圆心 R）
        const p1x = cx + R * cosA
        const p1y = cy + R * sinA
        // P2: 向外延伸一段（R + gap）
        const gap = 10
        const p2x = cx + (R + gap) * cosA
        const p2y = cy + (R + gap) * sinA
        // P3: 水平延伸终点
        const isRight = cosA >= -0.05
        const p3x = isRight
          ? p2x + 16 + item.label.length * 5.2
          : p2x - 16 - item.label.length * 5.2
        const p3y = p2y

        // polyPoints 用于画折线
        const polyPoints = `${p1x},${p1y} ${p2x},${p2y} ${p3x},${p3y}`

        // 标签文字位置（P3 外侧）
        const textOffset = 4
        const textX = isRight ? p3x + textOffset : p3x - textOffset
        const textY = p3y - 4.5
        const pctY = p3y + 5.5
        const anchor = isRight ? 'start' : 'end'

        labels.push({
          name: item.label,
          pct: `${Number(item.pct).toFixed(1)}%`,
          anchor,
          polyPoints,
          endX: p3x, endY: p3y,
          textX, textY, pctX: textX, pctY
        })

        angle += spanDeg
      }

      return labels
    }
  },
  methods: {
    getGradient(idx) {
      const p = COLOR_PAIRS[idx % COLOR_PAIRS.length]
      return `linear-gradient(90deg, ${p[0]}, ${p[1]})`
    },
    formatValue(val) {
      const n = Number(val)
      if (!Number.isFinite(n)) return val
      return n % 1 === 0 ? n.toLocaleString() : n.toFixed(1)
    }
  }
}
</script>

<style scoped>
.chart-container {
  margin: 16px 0; padding: 20px; background: #fff;
  border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,.06);
  border: 1px solid #eaeaea;
}
.chart-title { font-size: 15px; font-weight: 600; color: #1a1a1a; margin: 0 0 14px; text-align: center; }

/* ===== 柱状图 ===== */
.css-chart { width: 100%; }
.css-bar-row { display: flex; align-items: center; margin-bottom: 10px; gap: 12px; }
.css-bar-row:last-child { margin-bottom: 0; }
.css-label { flex-shrink: 0; width: 70px; text-align: right; font-size: 13px; font-weight: 500; color: #444; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.css-track { flex: 1; height: 30px; background: #ececec; border-radius: 15px; overflow: hidden; position: relative; }
.css-fill { height: 100%; display: flex; align-items: center; justify-content: flex-end; padding-right: 12px; min-width: 50px; transition: width .8s ease-out; border-radius: 15px; background: #667eea; }
.css-value { color: #fff; font-size: 12px; font-weight: 700; white-space: nowrap; text-shadow: 0 1px 2px rgba(0,0,0,.3); }

/* ===== 饼图 ===== */
.pie-wrapper { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 2px 0; }
.pie-svg { width: 100%; max-width: 300px; height: auto; overflow: visible; }

/* conic-gradient 饼图（通过 foreignObject 嵌入） */
.pie-circle {
  width: 100%; height: 100%;
  border-radius: 50%; transition: transform .25s, box-shadow .25s;
}
.pie-circle:hover {
  transform: scale(1.04);
  box-shadow: 0 4px 14px rgba(102,126,234,.15);
}

/* 饼图标签文字 */
.pie-label-txt { font-size: 10px; font-weight: 600; fill: #333; }
.pie-label-pct { font-size: 9px; font-weight: 500; fill: #777; }

/* 图例 */
.pie-legend-grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 4px 14px; max-width: 320px; }
.legend-cell { display: flex; align-items: center; gap: 3px; padding: 1px 3px; border-radius: 3px; cursor: default; transition: background .15s; }
.legend-cell:hover { background: #f5f5fa; }
.legend-dot { width: 8px; height: 8px; border-radius: 2px; flex-shrink: 0; }
.legend-name { font-size: 11px; font-weight: 500; color: #444; max-width: 54px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.legend-pct { font-size: 10px; color: #888; font-weight: 600; min-width: 28px; text-align: right; }

.chart-fallback { padding: 16px; text-align: center; color: #999; font-style: italic; }
</style>
