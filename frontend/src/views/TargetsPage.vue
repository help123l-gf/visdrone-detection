<template>
  <div class="targets-page">
    <div class="page-header">
      <h1 class="page-title">目标检测库</h1>
      <p class="page-subtitle">平台支持检测的所有 VisDrone 无人机航拍目标类别</p>
    </div>

    <div class="search-container">
      <el-input
        v-model="searchQuery"
        placeholder="搜索目标类别..."
        size="default"
        class="search-input"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon target-icon">
          <el-icon><Aim /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ totalTargets }}</div>
          <div class="stat-label">目标总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon category-icon">
          <el-icon><Grid /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ categories.length }}</div>
          <div class="stat-label">类别数量</div>
        </div>
      </div>
    </div>

    <div class="target-categories">
      <div
        v-for="category in filteredCategories"
        :key="category.id"
        class="category-card"
      >
        <div class="category-header">
          <div
            class="category-icon"
            :style="{ backgroundColor: category.color }"
          >
            <component :is="category.icon" />
          </div>
          <div class="category-info">
            <div class="category-name">{{ category.name }}</div>
            <div class="category-count">
              {{ category.targets.length }} 个目标
            </div>
          </div>
        </div>
        <div class="target-list">
          <div
            v-for="target in category.targets"
            :key="target.id"
            class="target-item"
            @click="showTargetDetail(target)"
          >
            <el-icon :size="14" class="target-item-icon"><CircleCheck /></el-icon>
            <span>{{ target.name }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="filteredCategories.length === 0" class="empty-state">
      <el-icon :size="64" class="empty-icon"><Folder /></el-icon>
      <p class="empty-text">未找到匹配的目标类别</p>
    </div>

    <el-dialog
      v-if="selectedTarget"
      v-model="showDialog"
      :title="selectedTarget.name"
      width="400px"
    >
      <div class="target-detail">
        <div class="detail-icon" :style="{ backgroundColor: getCategoryColor(selectedTarget.categoryId) }">
          <el-icon :size="48"><component :is="getCategoryIcon(selectedTarget.categoryId)" /></el-icon>
        </div>
        <div class="detail-info">
          <div class="detail-item">
            <span class="detail-label">所属类别</span>
            <span class="detail-value">{{ getCategoryName(selectedTarget.categoryId) }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">目标描述</span>
            <span class="detail-value">{{ selectedTarget.description }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">检测精度</span>
            <span class="detail-value">{{ selectedTarget.accuracy }}</span>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import {
  Search,
  Aim,
  Grid,
  CircleCheck,
  Folder,
  Bicycle,
  User,
  Setting,
} from "@element-plus/icons-vue";

const searchQuery = ref("");
const showDialog = ref(false);
const selectedTarget = ref(null);

const categories = ref([
  {
    id: 1,
    name: "行人目标",
    icon: User,
    color: "#3b82f6",
    targets: [
      { id: 0, name: "行人", categoryId: 1, description: "单个行人，无人机视角下的独立个体", accuracy: "89.2%" },
      { id: 1, name: "人群", categoryId: 1, description: "密集人群，含部分遮挡的目标集合", accuracy: "85.7%" },
    ],
  },
  {
    id: 2,
    name: "非机动车",
    icon: Bicycle,
    color: "#10b981",
    targets: [
      { id: 2, name: "自行车", categoryId: 2, description: "自行车及骑行者，无人机视角小目标", accuracy: "82.4%" },
      { id: 6, name: "三轮车", categoryId: 2, description: "人力或机动三轮车", accuracy: "78.9%" },
      { id: 7, name: "遮阳三轮车", categoryId: 2, description: "带遮阳棚的三轮车，常见于城市街景", accuracy: "76.3%" },
      { id: 9, name: "摩托车", categoryId: 2, description: "摩托车、电动车骑行者", accuracy: "84.1%" },
    ],
  },
  {
    id: 3,
    name: "机动车辆",
    icon: Setting,
    color: "#f59e0b",
    targets: [
      { id: 3, name: "汽车", categoryId: 3, description: "小轿车、SUV等乘用车", accuracy: "91.5%" },
      { id: 4, name: "面包车", categoryId: 3, description: "厢式货车、面包车", accuracy: "88.7%" },
      { id: 5, name: "卡车", categoryId: 3, description: "大型货运卡车、渣土车等", accuracy: "87.3%" },
      { id: 8, name: "公交车", categoryId: 3, description: "公共汽车、大巴客车", accuracy: "90.8%" },
    ],
  },
]);

const filteredCategories = computed(() => {
  if (!searchQuery.value) {
    return categories.value;
  }
  const query = searchQuery.value.toLowerCase();
  return categories.value.map((category) => ({
    ...category,
    targets: category.targets.filter((target) =>
      target.name.toLowerCase().includes(query)
    ),
  })).filter((category) =>
    category.name.toLowerCase().includes(query) || category.targets.length > 0
  );
});

const totalTargets = computed(() => {
  return categories.value.reduce((sum, category) => sum + category.targets.length, 0);
});

const getCategoryColor = (categoryId) => {
  const category = categories.value.find((c) => c.id === categoryId);
  return category ? category.color : "#6b7280";
};

const getCategoryIcon = (categoryId) => {
  const category = categories.value.find((c) => c.id === categoryId);
  return category ? category.icon : Setting;
};

const getCategoryName = (categoryId) => {
  const category = categories.value.find((c) => c.id === categoryId);
  return category ? category.name : "未知";
};

const showTargetDetail = (target) => {
  selectedTarget.value = target;
  showDialog.value = true;
};
</script>

<style scoped lang="scss">
.targets-page {
  width: 100%;

  .page-header {
    margin-bottom: 24px;

    .page-title {
      font-size: 24px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 8px;
    }

    .page-subtitle {
      font-size: 14px;
      color: var(--text-secondary);
    }
  }

  .search-container {
    margin-bottom: 24px;

    .search-input {
      max-width: 300px;
    }
  }

  .stats-cards {
    display: flex;
    gap: 20px;
    margin-bottom: 24px;

    .stat-card {
      flex: 1;
      max-width: 200px;
      background-color: #ffffff;
      border-radius: 12px;
      padding: 20px;
      box-shadow: var(--card-shadow);
      display: flex;
      align-items: center;
      gap: 16px;

      .stat-icon {
        width: 50px;
        height: 50px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 24px;

        &.target-icon {
          background-color: #27ae60;
        }

        &.category-icon {
          background-color: #3b82f6;
        }
      }

      .stat-info {
        .stat-value {
          font-size: 24px;
          font-weight: 600;
          color: var(--text-primary);
        }

        .stat-label {
          font-size: 13px;
          color: var(--text-secondary);
        }
      }
    }
  }

  .target-categories {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 24px;

    .category-card {
      background-color: #ffffff;
      border-radius: 12px;
      padding: 20px;
      box-shadow: var(--card-shadow);
      transition: all 0.2s;

      &:hover {
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
      }

      .category-header {
        display: flex;
        align-items: center;
        margin-bottom: 16px;

        .category-icon {
          width: 50px;
          height: 50px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-size: 24px;
          margin-right: 16px;
        }

        .category-info {
          .category-name {
            font-size: 18px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 4px;
          }

          .category-count {
            font-size: 13px;
            color: var(--text-secondary);
          }
        }
      }

      .target-list {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;

        .target-item {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 14px;
          background-color: #f3f4f6;
          border-radius: 20px;
          font-size: 14px;
          color: var(--text-secondary);
          cursor: pointer;
          transition: all 0.2s;

          &:hover {
            background-color: rgba(39, 174, 96, 0.1);
            color: #27ae60;
          }

          .target-item-icon {
            color: #27ae60;
          }
        }
      }
    }
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 0;

    .empty-icon {
      color: #9ca3af;
      margin-bottom: 16px;
    }

    .empty-text {
      font-size: 15px;
      color: var(--text-secondary);
    }
  }

  .target-detail {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px 0;

    .detail-icon {
      width: 80px;
      height: 80px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      margin-bottom: 20px;
    }

    .detail-info {
      width: 100%;

      .detail-item {
        display: flex;
        justify-content: space-between;
        padding: 12px 0;
        border-bottom: 1px solid #f3f4f6;

        &:last-child {
          border-bottom: none;
        }

        .detail-label {
          font-size: 14px;
          color: var(--text-secondary);
        }

        .detail-value {
          font-size: 14px;
          color: var(--text-primary);
          font-weight: 500;
        }
      }
    }
  }
}
</style>
