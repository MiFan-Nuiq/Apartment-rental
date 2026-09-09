<template>
  <div class="complaints">
    <el-card>
      <template #header><span>投诉建议管理</span></template>
      <el-form :inline="true" style="margin-bottom: 16px;">
        <el-form-item label="状态">
          <el-select v-model="filterStatus" placeholder="全部" clearable style="width: 120px;">
            <el-option label="待处理" value="待处理" />
            <el-option label="已处理" value="已处理" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filterType" placeholder="全部" clearable style="width: 120px;">
            <el-option label="投诉" value="投诉" />
            <el-option label="建议" value="建议" />
          </el-select>
        </el-form-item>
      </el-form>
      <el-table :data="filteredComplaints" v-loading="loading" stripe>
        <el-table-column prop="type" label="类型" min-width="80">
          <template #default="scope">
            <el-tag :type="scope.row.type === '投诉' ? 'danger' : 'primary'">{{ scope.row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="租客" min-width="100">
          <template #default="scope">{{ scope.row.tenant?.realName || scope.row.tenant?.username }}</template>
        </el-table-column>
        <el-table-column label="联系方式" min-width="120">
          <template #default="scope">{{ scope.row.tenant?.phone || '-' }}</template>
        </el-table-column>
        <el-table-column label="相关房源" min-width="120">
          <template #default="scope">{{ scope.row.apartment?.name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="content" label="内容" min-width="250" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" min-width="80">
          <template #default="scope">
            <el-tag :type="scope.row.status === '待处理' ? 'warning' : 'success'">{{ scope.row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="提交时间" min-width="140">
          <template #default="scope">{{ formatTime(scope.row.createTime) }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="100" fixed="right">
          <template #default="scope">
            <el-button v-if="scope.row.status === '待处理'" type="primary" size="small" @click="openReplyDialog(scope.row)">处理</el-button>
            <el-button v-else type="info" size="small" @click="openReplyDialog(scope.row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && complaints.length === 0" description="暂无投诉建议" />
    </el-card>

    <el-dialog v-model="replyDialogVisible" :title="currentComplaint?.status === '待处理' ? '处理投诉/建议' : '查看详情'" width="550px">
      <el-descriptions :column="1" border style="margin-bottom: 20px;">
        <el-descriptions-item label="类型">
          <el-tag :type="currentComplaint?.type === '投诉' ? 'danger' : 'primary'">{{ currentComplaint?.type }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="租客">{{ currentComplaint?.tenant?.realName || currentComplaint?.tenant?.username }}</el-descriptions-item>
        <el-descriptions-item label="联系方式">{{ currentComplaint?.tenant?.phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="相关房源">{{ currentComplaint?.apartment?.name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="提交时间">{{ formatTime(currentComplaint?.createTime) }}</el-descriptions-item>
        <el-descriptions-item label="内容">
          <div style="white-space: pre-wrap;">{{ currentComplaint?.content }}</div>
        </el-descriptions-item>
        <el-descriptions-item v-if="currentComplaint?.adminReply" label="回复内容">
          <div style="white-space: pre-wrap;">{{ currentComplaint?.adminReply }}</div>
        </el-descriptions-item>
        <el-descriptions-item v-if="currentComplaint?.replyTime" label="回复时间">{{ formatTime(currentComplaint?.replyTime) }}</el-descriptions-item>
      </el-descriptions>
      <el-form v-if="currentComplaint?.status === '待处理'" :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="回复内容" prop="reply">
          <el-input v-model="form.reply" type="textarea" :rows="4" placeholder="请输入回复内容" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="replyDialogVisible = false">关闭</el-button>
        <el-button v-if="currentComplaint?.status === '待处理'" type="primary" @click="handleSubmit">提交回复</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { getAllComplaints, replyComplaint } from '../../api'
import { ElMessage } from 'element-plus'

export default {
  name: 'AdminComplaints',
  data() {
    return {
      complaints: [],
      loading: false,
      filterStatus: '',
      filterType: '',
      replyDialogVisible: false,
      currentComplaint: null,
      form: { reply: '' },
      rules: {
        reply: [{ required: true, message: '请输入回复内容', trigger: 'blur' }]
      }
    }
  },
  computed: {
    filteredComplaints() {
      let result = this.complaints
      if (this.filterStatus) {
        result = result.filter(c => c.status === this.filterStatus)
      }
      if (this.filterType) {
        result = result.filter(c => c.type === this.filterType)
      }
      return result
    }
  },
  created() { this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const res = await getAllComplaints()
        this.complaints = res.data || []
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    openReplyDialog(row) {
      this.currentComplaint = row
      this.form.reply = row.adminReply || ''
      this.replyDialogVisible = true
    },
    handleSubmit() {
      this.$refs.formRef.validate(async (valid) => {
        if (valid) {
          await replyComplaint(this.currentComplaint.id, this.form.reply)
          ElMessage.success('回复成功')
          this.replyDialogVisible = false
          this.loadData()
        }
      })
    },
    formatTime(time) {
      if (!time) return '-'
      const date = new Date(time)
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
    }
  }
}
</script>
