<template>
  <div class="app-shell">
    <aside class="app-sidebar">
      <slot name="sidebar" />
    </aside>
    <div class="app-main">
      <header class="app-header">
        <slot name="header" />
      </header>
      <main class="app-content">
        <slot name="content" />
      </main>
    </div>
  </div>
</template>

<script setup></script>

<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.app-sidebar {
  width: var(--sidebar-width);
  background: var(--sidebar-bg);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.app-header {
  height: var(--header-height);
  background: var(--header-bg);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
  z-index: 10;
}

.app-content {
  flex: 1;
  background: var(--content-bg);
  overflow: auto;
}
</style>
