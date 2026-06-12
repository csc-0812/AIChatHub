<template>
  <div class="theme-toggle" :title="`当前主题：${currentInfo.label}`">
    <button class="theme-btn" @click="cycleTheme">
      <span class="theme-icon">{{ currentInfo.icon }}</span>
    </button>
    <!-- 下拉 -->
    <div v-if="showDropdown" class="theme-dropdown">
      <div
        v-for="(info, key) in THEMES"
        :key="key"
        class="theme-dropdown-item"
        :class="{ active: activeTheme === key }"
        @click="selectTheme(key)"
      >
        <span class="theme-item-icon">{{ info.icon }}</span>
        <span class="theme-item-label">{{ info.label }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import { THEMES, getSavedTheme, setTheme, getThemeInfo } from '../themes/theme.js'

export default {
  name: 'ThemeToggle',
  data() {
    return {
      THEMES,
      activeTheme: getSavedTheme(),
      showDropdown: false
    }
  },
  computed: {
    currentInfo() {
      return getThemeInfo(this.activeTheme)
    }
  },
  mounted() {
    document.addEventListener('click', this.closeDropdown)
  },
  beforeDestroy() {
    document.removeEventListener('click', this.closeDropdown)
  },
  methods: {
    cycleTheme() {
      const keys = Object.keys(THEMES)
      const idx = keys.indexOf(this.activeTheme)
      const next = keys[(idx + 1) % keys.length]
      this.selectTheme(next)
    },
    selectTheme(key) {
      this.activeTheme = setTheme(key)
      this.showDropdown = false
    },
    toggleDropdown() {
      this.showDropdown = !this.showDropdown
    },
    closeDropdown(e) {
      const el = this.$el
      if (el && !el.contains(e.target)) {
        this.showDropdown = false
      }
    }
  }
}
</script>

<style scoped>
.theme-toggle {
  position: relative;
}

.theme-btn {
  background: none;
  border: 1px solid var(--card-border, #334155);
  border-radius: 8px;
  cursor: pointer;
  padding: 6px 10px;
  font-size: 16px;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted, #94a3b8);
}

.theme-btn:hover {
  background: var(--brand-bg, rgba(30, 80, 229, 0.12));
  border-color: var(--brand, #1E50E5);
  color: var(--text-primary, #f1f5f9);
}

.theme-icon {
  line-height: 1;
}

/* 下拉 */
.theme-dropdown {
  position: absolute;
  right: 0;
  top: 100%;
  margin-top: 6px;
  background: var(--dropdown-bg, #1e293b);
  border: 1px solid var(--dropdown-border, #334155);
  border-radius: 10px;
  box-shadow: var(--shadow-dropdown, 0 4px 24px rgba(0, 0, 0, 0.4));
  min-width: 160px;
  z-index: 1001;
  overflow: hidden;
}

.theme-dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary, #cbd5e1);
  transition: all 0.12s ease;
}

.theme-dropdown-item:hover {
  background: var(--brand-bg, rgba(30, 80, 229, 0.12));
  color: var(--text-primary, #f1f5f9);
}

.theme-dropdown-item.active {
  background: var(--brand-bg, rgba(30, 80, 229, 0.12));
  color: var(--brand-light, #6EA8FF);
}

.theme-item-icon {
  font-size: 16px;
}
</style>
