<template>
  <div class="reviews">
    <el-card>
      <template #header><span>评价管理</span></template>
      <el-form :inline="true" style="margin-bottom: 16px;">
        <el-form-item label="审核状态">
          <el-select v-model="filterStatus" placeholder="全部" clearable style="width: 120px;">
            <el-option label="待审核" value="待审核" />
            <el-option label="已通过" value="已通过" />
            <el-option label="已拒绝" value="已拒绝" />
          </el-select>
        </el-form-item>
      </el-form>
      <el-table :data="filteredReviews" v-loading="loading" stripe>
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
        <el-table-column prop="content" label="评价内容" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="审核状态" min-width="90">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="提交时间" min-width="140">
          <template #default="scope">{{ formatTime(scope.row.createTime) }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="150" fixed="right">
          <template #default="scope">
            <template v-if="scope.row.status === '待审核'">
              <el-button type="success" size="small" @click="handleAudit(scope.row, '已通过')">通过</el-button>
              <el-button type="danger" size="small" @click="openRejectDialog(scope.row)">拒绝</el-button>
            </template>
            <el-button v-else type="info" size="small" @click="viewDetail(scope.row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && reviews.length === 0" description="暂无评价" />
    </el-card>

    <el-dialog v-model="rejectDialogVisible" title="拒绝评价" width="450px">
      <el-form :model="rejectForm" :rules="rejectRules" ref="rejectFormRef" label-width="80px">
        <el-form-item label="拒绝原因" prop="remark">
          <el-input v-model="rejectForm.remark" type="textarea" :rows="3" placeholder="请输入拒绝原因" maxlength="200" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmReject">确认拒绝</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailDialogVisible" title="评价详情" width="550px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="房源">{{ currentReview?.apartment?.name }}</el-descriptions-item>
        <el-descriptions-item label="租客">{{ currentReview?.tenant?.realName || currentReview?.tenant?.username }}</el-descriptions-item>
        <el-descriptions-item label="评分">
          <el-rate v-model="currentReview.rating" disabled />
        </el-descriptions-item>
        <el-descriptions-item label="评价内容">
          <div style="white-space: pre-wrap;">{{ currentReview?.content }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="审核状态">
          <el-tag :type="getStatusType(currentReview?.status)">{{ currentReview?.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item v-if="currentReview?.auditRemark" label="审核备注">{{ currentReview?.auditRemark }}</el-descriptions-item>
        <el-descriptions-item label="提交时间">{{ formatTime(currentReview?.createTime) }}</el-descriptions-item>
        <el-descriptions-item v-if="currentReview?.landlordReply" label="房东回复">{{ currentReview?.landlordReply }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { getReviews, auditReview } from '../../api'
import { ElMessage } from 'element-plus'

export default {
  name: 'AdminReviews',
  data() {
    return {
      reviews: [],
      loading: false,
      filterStatus: '',
      rejectDialogVisible: false,
      currentReview: null,
      rejectForm: { remark: '' },
      rejectRules: { remark: [{ required: true, message: '请输入拒绝原因', trigger: 'blur' }] },
      detailDialogVisible: false
    }
  },
  computed: {
    filteredReviews() {
      if (!this.filterStatus) return this.reviews
      return this.reviews.filter(r => r.status === this.filterStatus)
    }
  },
  created() { this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const res = await getReviews()
        this.reviews = res.data || []
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    async handleAudit(row, status) {
      try {
        await auditReview(row.id, status, '')
        ElMessage.success('审核通过')
        this.loadData()
      } catch (e) { console.error(e) }
    },
    openRejectDialog(row) {
      this.currentReview = row
      this.rejectForm.remark = ''
      this.rejectDialogVisible = true
    },
    confirmReject() {
      this.$refs.rejectFormRef.validate(async (valid) => {
        if (valid) {
          await auditReview(this.currentReview.id, '已拒绝', this.rejectForm.remark)
          ElMessage.success('已拒绝该评价')
          this.rejectDialogVisible = false
          this.loadData()
        }
      })
    },
    viewDetail(row) {
      this.currentReview = row
      this.detailDialogVisible = true
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
