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
        <el-tab-pane label="我的评价" name="reviews">
          <div style="margin-bottom: 16px;">
            <el-button type="primary" @click="openReviewDialog">发表评价</el-button>
          </div>
          <el-table :data="reviews" v-loading="loading">
            <el-table-column label="房源" min-width="140">
              <template #default="scope">
                <div>{{ scope.row.apartment?.name }}</div>
                <div style="color: #909399; font-size: 12px;">{{ scope.row.apartment?.address }}</div>
              </template>
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
            <el-table-column label="评价时间" min-width="140">
              <template #default="scope">{{ formatTime(scope.row.createTime) }}</template>
            </el-table-column>
            <el-table-column label="房东回复" min-width="150">
              <template #default="scope">{{ scope.row.landlordReply || '-' }}</template>
            </el-table-column>
            <el-table-column label="操作" min-width="80">
              <template #default="scope">
                <el-button size="small" type="danger" link @click="handleDeleteReview(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!loading && reviews.length === 0" description="暂无评价" />
        </el-tab-pane>
        <el-tab-pane label="投诉建议" name="complaints">
          <div style="margin-bottom: 16px;">
            <el-button type="primary" @click="openComplaintDialog">提交投诉/建议</el-button>
          </div>
          <el-table :data="complaints" v-loading="loading">
            <el-table-column prop="type" label="类型" min-width="80">
              <template #default="scope">
                <el-tag :type="scope.row.type === '投诉' ? 'danger' : 'primary'">{{ scope.row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="content" label="内容" min-width="200" show-overflow-tooltip />
            <el-table-column label="相关房源" min-width="120">
              <template #default="scope">{{ scope.row.apartment?.name || '-' }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" min-width="80">
              <template #default="scope">
                <el-tag :type="scope.row.status === '待处理' ? 'warning' : 'success'">{{ scope.row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="提交时间" min-width="140">
              <template #default="scope">{{ formatTime(scope.row.createTime) }}</template>
            </el-table-column>
            <el-table-column label="管理员回复" min-width="150">
              <template #default="scope">{{ scope.row.adminReply || '-' }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!loading && complaints.length === 0" description="暂无投诉建议" />
        </el-tab-pane>
        <el-tab-pane label="发送消息" name="send">
          <el-form :model="sendForm" :rules="sendRules" ref="sendFormRef" label-width="80px">
            <el-form-item label="接收人" prop="receiverId">
              <el-select v-model="sendForm.receiverId" placeholder="请选择接收人" style="width: 100%" filterable>
                <el-option v-for="user in landlords" :key="user.id" :label="`${user.realName} (${user.phone})`" :value="user.id" />
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

    <el-dialog v-model="reviewDialogVisible" title="发表评价" width="500px">
      <el-form :model="reviewForm" :rules="reviewRules" ref="reviewFormRef" label-width="80px">
        <el-form-item label="选择合同" prop="contractId">
          <el-select v-model="reviewForm.contractId" placeholder="请选择已结束的合同" style="width: 100%" @change="handleContractChange">
            <el-option v-for="c in endedContracts" :key="c.id" :label="`${c.apartment?.name} (${c.startDate} ~ ${c.endDate})`" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="房源">
          <el-input :value="selectedContract?.apartment?.name" disabled />
        </el-form-item>
        <el-form-item label="评分" prop="rating">
          <el-rate v-model="reviewForm.rating" show-text />
        </el-form-item>
        <el-form-item label="评价内容" prop="content">
          <el-input v-model="reviewForm.content" type="textarea" :rows="4" placeholder="请输入评价内容，提交后需管理员审核" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitReview">提交评价</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="complaintDialogVisible" title="提交投诉/建议" width="500px">
      <el-form :model="complaintForm" :rules="complaintRules" ref="complaintFormRef" label-width="80px">
        <el-form-item label="类型" prop="type">
          <el-radio-group v-model="complaintForm.type">
            <el-radio label="投诉">投诉</el-radio>
            <el-radio label="建议">建议</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="相关房源">
          <el-select v-model="complaintForm.apartmentId" placeholder="可选" clearable style="width: 100%">
            <el-option v-for="a in apartments" :key="a.id" :label="a.name" :value="a.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="complaintForm.content" type="textarea" :rows="4" placeholder="请详细描述您的问题或建议" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="complaintDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitComplaint">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { getAnnouncements, getMessagesByReceiver, createMessage, markMessageAsRead, deleteMessage, getUsers, getTenantReviews, getContractsByTenant, createReview, deleteReview, getComplaints, createComplaint, getApartments } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'TenantMessages',
  data() {
    return {
      announcements: [],
      messages: [],
      reviews: [],
      complaints: [],
      landlords: [],
      apartments: [],
      endedContracts: [],
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
      reviewDialogVisible: false,
      selectedContract: null,
      reviewForm: { contractId: null, rating: 5, content: '' },
      reviewRules: {
        contractId: [{ required: true, message: '请选择合同', trigger: 'change' }],
        rating: [{ required: true, message: '请选择评分', trigger: 'change' }],
        content: [{ required: true, message: '请输入评价内容', trigger: 'blur' }]
      },
      complaintDialogVisible: false,
      complaintForm: { type: '建议', apartmentId: null, content: '' },
      complaintRules: {
        type: [{ required: true, message: '请选择类型', trigger: 'change' }],
        content: [{ required: true, message: '请输入内容', trigger: 'blur' }]
      }
    }
  },
  created() { this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const userId = localStorage.getItem('userId')
        const [ann, msg, users, rev, con, apt, comp] = await Promise.all([
          getAnnouncements('TENANT'),
          getMessagesByReceiver(userId),
          getUsers(),
          getTenantReviews(userId),
          getContractsByTenant(userId),
          getApartments(),
          getComplaints(userId)
        ])
        this.announcements = ann.data
        this.messages = msg.data.filter(m => m.type !== '公告')
        this.landlords = users.data.filter(u => u.role === 'LANDLORD')
        this.reviews = rev.data || []
        this.complaints = comp.data || []
        this.apartments = apt.data || []
        this.endedContracts = con.data.filter(c => c.status === '已到期' || c.status === '已终止')
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
      await deleteMessage(row.id)
      ElMessage.success('删除成功')
      this.dialogVisible = false
      this.loadData()
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
    openReviewDialog() {
      if (this.endedContracts.length === 0) {
        ElMessage.warning('暂无可评价的合同，只有已到期或已终止的合同才能评价')
        return
      }
      this.selectedContract = null
      this.reviewForm = { contractId: null, rating: 5, content: '' }
      this.reviewDialogVisible = true
    },
    handleContractChange(contractId) {
      this.selectedContract = this.endedContracts.find(c => c.id === contractId)
    },
    submitReview() {
      this.$refs.reviewFormRef.validate(async (valid) => {
        if (valid) {
          const userId = localStorage.getItem('userId')
          await createReview({
            tenantId: userId,
            apartmentId: this.selectedContract.apartment.id,
            contractId: this.selectedContract.id,
            rating: this.reviewForm.rating,
            content: this.reviewForm.content
          })
          ElMessage.success('评价已提交，等待管理员审核')
          this.reviewDialogVisible = false
          this.loadData()
        }
      })
    },
    handleDeleteReview(row) {
      ElMessageBox.confirm('确定要删除该评价吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        const userId = localStorage.getItem('userId')
        await deleteReview(row.id, userId)
        ElMessage.success('删除成功')
        this.loadData()
      }).catch(() => {})
    },
    openComplaintDialog() {
      this.complaintForm = { type: '建议', apartmentId: null, content: '' }
      this.complaintDialogVisible = true
    },
    submitComplaint() {
      this.$refs.complaintFormRef.validate(async (valid) => {
        if (valid) {
          const userId = localStorage.getItem('userId')
          await createComplaint({
            tenant: { id: userId },
            apartment: this.complaintForm.apartmentId ? { id: this.complaintForm.apartmentId } : null,
            type: this.complaintForm.type,
            content: this.complaintForm.content
          })
          ElMessage.success('提交成功')
          this.complaintDialogVisible = false
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
