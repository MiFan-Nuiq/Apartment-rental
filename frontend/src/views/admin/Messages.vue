<template>
  <div class="messages">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>发布公告</span>
        </div>
      </template>
      <el-form :model="form" :rules="rules" ref="msgForm" label-width="80px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入公告标题" />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="5" placeholder="请输入公告内容" />
        </el-form-item>
        <el-form-item label="目标用户" prop="targetRole">
          <el-select v-model="form.targetRole" placeholder="请选择目标用户" style="width: 100%">
            <el-option label="全部用户" value="全部" />
            <el-option label="房东" value="LANDLORD" />
            <el-option label="租户" value="TENANT" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handlePublish">发布公告</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header><span>历史公告</span></template>
      <el-table :data="messages" v-loading="loading">
        <el-table-column prop="title" label="标题" width="180" />
        <el-table-column prop="content" label="内容" />
        <el-table-column label="目标用户" width="100">
          <template #default="scope">
            <el-tag>{{ getTargetRoleName(scope.row.targetRole) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="发布时间" width="180" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="scope">
            <el-button size="small" type="danger" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { getAnnouncements, createMessage, deleteMessage } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'AdminMessages',
  data() {
    return {
      messages: [],
      loading: false,
      form: { title: '', content: '', targetRole: '全部' },
      rules: {
        title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
        content: [{ required: true, message: '请输入内容', trigger: 'blur' }],
        targetRole: [{ required: true, message: '请选择目标用户', trigger: 'change' }]
      }
    }
  },
  created() { this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try { this.messages = (await getAnnouncements()).data } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    handlePublish() {
      this.$refs.msgForm.validate(async (valid) => {
        if (valid) {
          try {
            await createMessage({ 
              title: this.form.title, 
              content: this.form.content, 
              targetRole: this.form.targetRole,
              type: '公告', 
              sender: { id: localStorage.getItem('userId') } 
            })
            ElMessage.success('发布成功')
            this.form = { title: '', content: '', targetRole: '全部' }
            this.loadData()
          } catch (e) { console.error(e) }
        }
      })
    },
    handleDelete(row) {
      ElMessageBox.confirm('确定要删除该公告吗？', '提示', { type: 'warning' }).then(async () => {
        await deleteMessage(row.id)
        ElMessage.success('删除成功')
        this.loadData()
      }).catch(() => {})
    },
    getTargetRoleName(role) {
      const names = { '全部': '全部用户', 'LANDLORD': '房东', 'TENANT': '租户' }
      return names[role] || role
    }
  }
}
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
