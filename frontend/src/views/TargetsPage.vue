<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">目标分类库</h1>
      <p class="page-desc">VisDrone 数据集支持的 10 类无人机航拍检测目标</p>
    </div>

    <div class="stats-row-top">
      <div class="stat-mini"><span class="sn">{{ totalTargets }}</span><span class="sl">目标总数</span></div>
      <div class="stat-mini"><span class="sn">{{ categories.length }}</span><span class="sl">类别数量</span></div>
      <div class="stat-mini"><span class="sn">YOLO11m</span><span class="sl">检测模型</span></div>
      <div class="stat-mini"><span class="sn">VisDrone</span><span class="sl">数据集</span></div>
    </div>

    <div class="category-grid">
      <div v-for="cat in categories" :key="cat.id" class="category-card">
        <div class="cat-header">
          <div class="cat-icon" :style="{background:cat.color}">
            <el-icon :size="20"><component :is="cat.icon" /></el-icon>
          </div>
          <div>
            <div class="cat-name">{{ cat.name }}</div>
            <div class="cat-count">{{ cat.targets.length }} 个目标</div>
          </div>
        </div>
        <div class="target-tags">
          <span v-for="t in cat.targets" :key="t.id" class="target-chip" @click="showDetail(t)">
            {{ t.name }}
          </span>
        </div>
      </div>
    </div>

    <el-dialog v-if="selected" v-model="dialogVisible" :title="selected.name" width="380px" align-center>
      <div class="detail-body">
        <div class="detail-icon-big" :style="{background: getCatById(selected.categoryId)?.color}">
          <el-icon :size="36"><component :is="getCatById(selected.categoryId)?.icon" /></el-icon>
        </div>
        <div class="detail-rows">
          <div class="dr"><span>所属类别</span><span>{{ getCatById(selected.categoryId)?.name }}</span></div>
          <div class="dr"><span>描述</span><span>{{ selected.description }}</span></div>
          <div class="dr"><span>类别ID</span><span>{{ selected.id }}</span></div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { User, Bicycle, Setting } from "@element-plus/icons-vue";

const dialogVisible = ref(false);
const selected = ref(null);

const categories = ref([
  {
    id: 1, name: "行人目标", icon: User, color: "#3b82f6",
    targets: [
      { id: 0, name: "行人", categoryId: 1, description: "单个行人，无人机视角下的独立个体" },
      { id: 1, name: "人群", categoryId: 1, description: "密集人群，含部分遮挡的目标集合" },
    ],
  },
  {
    id: 2, name: "非机动车", icon: Bicycle, color: "#10b981",
    targets: [
      { id: 2, name: "自行车", categoryId: 2, description: "自行车及骑行者，无人机视角小目标" },
      { id: 6, name: "三轮车", categoryId: 2, description: "人力或机动三轮车" },
      { id: 7, name: "遮阳三轮车", categoryId: 2, description: "带遮阳棚的三轮车，常见于城市街景" },
      { id: 9, name: "摩托车", categoryId: 2, description: "摩托车、电动车骑行者" },
    ],
  },
  {
    id: 3, name: "机动车辆", icon: Setting, color: "#f59e0b",
    targets: [
      { id: 3, name: "汽车", categoryId: 3, description: "小轿车、SUV等乘用车" },
      { id: 4, name: "面包车", categoryId: 3, description: "厢式货车、面包车" },
      { id: 5, name: "卡车", categoryId: 3, description: "大型货运卡车" },
      { id: 8, name: "公交车", categoryId: 3, description: "公共汽车、大巴客车" },
    ],
  },
]);

const totalTargets = computed(() => categories.value.reduce((s, c) => s + c.targets.length, 0));
const getCatById = (id) => categories.value.find(c => c.id === id);
const showDetail = (t) => { selected.value = t; dialogVisible.value = true; };
</script>

<style scoped>
.page-container { padding: 24px; height: 100%; overflow-y: auto; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 20px; font-weight: 600; }
.page-desc { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

.stats-row-top { display: flex; gap: 16px; margin-bottom: 24px; }
.stat-mini {
  flex: 1; max-width: 180px; background: #fff; border-radius: 10px;
  box-shadow: var(--card-shadow); padding: 16px 20px; display: flex; flex-direction: column;
}
.sn { font-size: 22px; font-weight: 700; color: var(--primary); }
.sl { font-size: 12px; color: var(--text-muted); margin-top: 4px; }

.category-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.category-card {
  background: #fff; border-radius: 10px; box-shadow: var(--card-shadow);
  padding: 20px; transition: box-shadow 0.2s;
}
.category-card:hover { box-shadow: var(--card-shadow-hover); }
.cat-header { display: flex; align-items: center; gap: 14px; margin-bottom: 16px; }
.cat-icon {
  width: 44px; height: 44px; border-radius: 10px; display: flex;
  align-items: center; justify-content: center; color: #fff;
}
.cat-name { font-size: 16px; font-weight: 600; }
.cat-count { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

.target-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.target-chip {
  padding: 6px 14px; background: #f3f4f6; border-radius: 20px;
  font-size: 13px; color: var(--text-secondary); cursor: pointer;
  transition: all 0.15s;
}
.target-chip:hover { background: var(--primary-light); color: var(--primary); }

.detail-body { text-align: center; padding: 8px 0; }
.detail-icon-big {
  width: 72px; height: 72px; border-radius: 50%; display: flex;
  align-items: center; justify-content: center; color: #fff; margin: 0 auto 20px;
}
.detail-rows { text-align: left; }
.dr { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f3f4f6; font-size: 13px; }
.dr span:first-child { color: var(--text-secondary); }
.dr span:last-child { font-weight: 500; }
</style>
