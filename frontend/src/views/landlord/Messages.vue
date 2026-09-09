<template>
  <div class="messages">
    <el-card>
      <template #header><span>消息中心</span></template>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="公告通知" name="announcements">
          <el-table :data="announcements" v-loading="loading">
            <el-table-column prop="title" label="标题" min-width="150" />
            <el-table-column prop="content" label="内容" min-width="250" show-overflow-tooltip />
            <el-table-column label="发布时间" min-width="140">
              <template #default="scope">{{ formatTime(scope.row.createTime) }}</template>
            </el-table-column>
            <el-table-column label="操作" min-width="80">
              <template #default="scope">
                <el-button size="small" type="primary" link @click="viewAnnouncement(scope.row)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="我的消息" name="messages">
          <el-table :data="messages" v-loading="loading">
            <el-table-column prop="title" label="标题" min-width="150" />
            <el-table-column prop="content" label="内容" min-width="200" show-overflow-tooltip />
            <el-table-column prop="status" label="状态" min-width="80">
              <template #default="scope">
                <el-tag :type="scope.row.status === '已读' ? 'success' : 'warning'">{{ scope.row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="时间" min-width="140">
              <template #default="scope">{{ formatTime(scope.row.createTime) }}</template>
            </el-table-column>
            <el-table-column label="操作" min-width="150">
              <template #default="scope">
                <el-button size="small" type="primary" link @click="viewMessage(scope.row)">查看</el-button>
                <el-button size="small" type="success" link @click="handleRead(scope.row)" :disabled="scope.row.status === '已读'">已读</el-button>
                <el-button size="small" type="danger" link @click="handleDelete(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="租客评价" name="reviews">
          <el-table :data="reviews" v-loading="loading">
            <el-table-column label="房源" min-width="140">
              <template #default="scope">
                <div>{{ scope.row.apartment?.name }}</div>
                <div style="color: #909399; font-size: 12px;">{{ scope.row.apartment?.address }}</div>
              </template>
            </el-table-column>
            <el-table-column label="租客" min-width="100">
              <template #default="scope">{{ scope.row.tenant?.realName || scope.row.tenant?.username }}</template>
            </el-table-column>
            <el-table-column label="评分" min-width="120">
              <template #default="scope">
                <el-rate v-model="scope.row.rating" disabled />
              </template>
            </el-table-column>
            <el-table-column prop="content" label="评价内容" min-width="180" show-overflow-tooltip />
            <el-table-column label="审核状态" min-width="90">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="回复状态" min-width="90">
              <template #default="scope">
                <el-tag :type="scope.row.landlordReply ? 'success' : 'warning'">
                  {{ scope.row.landlordReply ? '已回复' : '待回复' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" min-width="80">
              <template #default="scope">
                <el-button v-if="scope.row.status === '已通过'" type="primary" size="small" @click="openReplyDialog(scope.row)">回复</el-button>
                <span v-else style="color: #909399;">等待审核</span>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!loading && reviews.length === 0" description="暂无评价" />
        </el-tab-pane>
        <el-tab-pane label="发送消息" name="send">
          <el-form :model="sendForm" :rules="sendRules" ref="sendFormRef" label-width="80px">
            <el-form-item label="接收人" prop="receiverId">
              <el-select v-model="sendForm.receiverId" placeholder="请选择接收人" style="width: 100%" filterable>
                <el-option v-for="user in tenants" :key="user.id" :label="`${user.realName} (${user.phone})`" :value="user.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="标题" prop="title">
              <el-input v-model="sendForm.title" placeholder="请输入消息标题" />
            </el-form-item>
            <el-form-item label="内容" prop="content">
              <el-input v-model="sendForm.content" type="textarea" :rows="4" placeholder="请输入消息内容" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSend">发送消息</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="currentMessage.title" width="500px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="发送人">{{ currentMessage.sender?.realName || '系统' }}</el-descriptions-item>
        <el-descriptions-item label="发送时间">{{ formatTime(currentMessage.createTime) }}</el-descriptions-item>
        <el-descriptions-item label="消息状态">
          <el-tag :type="currentMessage.status === '已读' ? 'success' : 'warning'">{{ currentMessage.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="消息内容">
          <div style="white-space: pre-wrap;">{{ currentMessage.content }}</div>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="dialogVisible = false">关闭</el-button>
        <el-button type="success" @click="handleRead(currentMessage)" :disabled="currentMessage.status === '已读'">标记已读</el-button>
        <el-button type="danger" @click="handleDelete(currentMessage)">删除</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="announcementDialogVisible" :title="currentAnnouncement.title" width="500px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="发布时间">{{ formatTime(currentAnnouncement.createTime) }}</el-descriptions-item>
        <el-descriptions-item label="公告内容">
          <div style="white-space: pre-wrap;">{{ currentAnnouncement.content }}</div>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="announcementDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="replyDialogVisible" title="回复评价" width="500px">
      <el-descriptions :column="1" border style="margin-bottom: 20px;">
        <el-descriptions-item label="房源">{{ currentReview?.apartment?.name }}</el-descriptions-item>
        <el-descriptions-item label="租客">{{ currentReview?.tenant?.realName || currentReview?.tenant?.username }}</el-descriptions-item>
        <el-descriptions-item label="评分">
          <el-rate v-model="currentReview.rating" disabled />
        </el-descriptions-item>
        <el-descriptions-item label="评价内容">{{ currentReview?.content }}</el-descriptions-item>
        <el-descriptions-item label="评价时间">{{ formatTime(currentReview?.createTime) }}</el-descriptions-item>
      </el-descriptions>
      <el-form :model="replyForm" :rules="replyRules" ref="replyFormRef" label-width="80px">
        <el-form-item label="回复内容" prop="reply">
          <el-input v-model="replyForm.reply" type="textarea" :rows="4" placeholder="请输入回复内容" maxlength="300" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="replyDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitReply">提交回复</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { getAnnouncements, getMessagesByReceiver, createMessage, markMessageAsRead, deleteMessage, getUsers, getLandlordReviews, replyReview } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'LandlordMessages',
  data() {
    return {
      announcements: [],
      messages: [],
      reviews: [],
      tenants: [],
      loading: false,
      activeTab: 'announcements',
      sendForm: { receiverId: null, title: '', content: '' },
      sendRules: {
        receiverId: [{ required: true, message: '请选择接收人', trigger: 'change' }],
        title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
        content: [{ required: true, message: '请输入内容', trigger: 'blur' }]
      },
      dialogVisible: false,
      currentMessage: {},
      announcementDialogVisible: false,
      currentAnnouncement: {},
      replyDialogVisible: false,
      currentReview: null,
      replyForm: { reply: '' },
      replyRules: { reply: [{ required: true, message: '请输入回复内容', trigger: 'blur' }] }
    }
  },
  created() { this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const userId = localStorage.getItem('userId')
        const [ann, msg, users, rev] = await Promise.all([
          getAnnouncements('LANDLORD'),
          getMessagesByReceiver(userId),
          getUsers(),
          getLandlordReviews(userId)
        ])
        this.announcements = ann.data
        this.messages = msg.data.filter(m => m.type !== '公告')
        this.tenants = users.data.filter(u => u.role === 'TENANT')
        this.reviews = rev.data || []
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    viewMessage(row) {
      this.currentMessage = row
      this.dialogVisible = true
    },
    viewAnnouncement(row) {
      this.currentAnnouncement = row
      this.announcementDialogVisible = true
    },
    async handleRead(row) {
      await markMessageAsRead(row.id)
      ElMessage.success('已标记为已读')
      this.dialogVisible = false
      this.loadData()
    },
    async handleDelete(row) {
      ElMessageBox.confirm('确定要删除此消息吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        await deleteMessage(row.id)
        ElMessage.success('删除成功')
        this.dialogVisible = false
        this.loadData()
      }).catch(() => {})
    },
    handleSend() {
      this.$refs.sendFormRef.validate(async (valid) => {
        if (valid) {
          try {
            const userId = localStorage.getItem('userId')
            await createMessage({
              title: this.sendForm.title,
              content: this.sendForm.content,
              type: '私信',
              sender: { id: userId },
              receiver: { id: this.sendForm.receiverId }
            })
            ElMessage.success('发送成功')
            this.sendForm = { receiverId: null, title: '', content: '' }
            this.activeTab = 'messages'
            this.loadData()
          } catch (e) { console.error(e) }
        }
      })
    },
    openReplyDialog(row) {
      this.currentReview = row
      this.replyForm.reply = row.landlordReply || ''
      this.replyDialogVisible = true
    },
    handleSubmitReply() {
      this.$refs.replyFormRef.validate(async (valid) => {
        if (valid) {
          await replyReview(this.currentReview.id, this.replyForm.reply)
          ElMessage.success('回复成功')
          this.replyDialogVisible = false
          this.loadData()
        }
      })
    },
    getStatusType(status) {
      return { '待审核': 'warning', '已通过': 'success', '已拒绝': 'danger' }[status] || 'info'
    },
    formatTime(time) {
      if (!time) return '-'
      const date = new Date(time)
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
    }
  }
}
</script>
