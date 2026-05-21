<template>
  <div class="qa-page">
    <div class="page-header">
      <h1 class="page-title">AI 智能问答</h1>
      <p class="page-subtitle">关于无人机视觉目标检测的任何问题，都可以问我</p>
    </div>

    <div class="chat-container">
      <div class="chat-messages" ref="chatMessagesRef">
        <div class="message ai-message">
          <div class="message-avatar">
            <el-icon><ChatDotRound /></el-icon>
          </div>
          <div class="message-content">
            你好！我是无人机视觉检测AI助手。我可以帮你解答关于行人、人群、自行车、汽车、面包车、卡车、三轮车、遮阳三轮车、公交车、摩托车等无人机航拍目标检测的相关问题，也可以为你提供检测结果的详细分析。
          </div>
        </div>

        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="message"
          :class="msg.role === 'user' ? 'user-message' : 'ai-message'"
        >
          <div class="message-avatar">
            <el-icon v-if="msg.role === 'ai'"><ChatDotRound /></el-icon>
            <el-icon v-else><User /></el-icon>
          </div>
          <div class="message-content">{{ msg.content }}</div>
        </div>
      </div>

      <div class="chat-input">
        <el-input
          v-model="question"
          placeholder="请输入你的问题..."
          :rows="3"
          type="textarea"
          @keydown.enter.exact="handleSend"
        />
        <el-button type="primary" class="send-btn" :loading="sending" @click="handleSend">
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from "vue";
import { ChatDotRound, User } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";

const question = ref("");
const sending = ref(false);
const messages = ref([]);
const chatMessagesRef = ref(null);

const handleSend = async () => {
  if (!question.value.trim()) return;

  const userMsg = question.value.trim();
  messages.value.push({ role: "user", content: userMsg });
  question.value = "";
  sending.value = true;

  await nextTick();
  if (chatMessagesRef.value) {
    chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight;
  }

  setTimeout(() => {
    messages.value.push({
      role: "ai",
      content: "感谢您的提问！这是一个模拟回复。Day3 将接入真实的 AI 问答功能。",
    });
    sending.value = false;
    nextTick(() => {
      if (chatMessagesRef.value) {
        chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight;
      }
    });
  }, 1000);
};
</script>

<style scoped lang="scss">
.qa-page {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;

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

  .chat-container {
    flex: 1;
    background-color: #ffffff;
    border-radius: 10px;
    box-shadow: var(--card-shadow);
    display: flex;
    flex-direction: column;
    min-height: 0;

    .chat-messages {
      flex: 1;
      padding: 20px;
      overflow-y: auto;

      .message {
        display: flex;
        margin-bottom: 20px;

        .message-avatar {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background-color: var(--primary-color);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 12px;
          flex-shrink: 0;
        }

        .message-content {
          background-color: #f3f4f6;
          padding: 12px 16px;
          border-radius: 0 12px 12px 12px;
          max-width: 70%;
          line-height: 1.6;
          font-size: 14px;
        }

        &.user-message {
          flex-direction: row-reverse;

          .message-avatar {
            margin-right: 0;
            margin-left: 12px;
            background-color: #60a5fa;
          }

          .message-content {
            background-color: var(--primary-light);
            border-radius: 12px 0 12px 12px;
          }
        }
      }
    }

    .chat-input {
      padding: 20px;
      border-top: 1px solid var(--border-color);
      display: flex;
      gap: 12px;

      .el-textarea {
        flex: 1;
      }

      .send-btn {
        width: 100px;
        height: auto;
      }
    }
  }
}
</style>
