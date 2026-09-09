<template>
  <div class="users">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户列表</span>
          <el-button type="primary" @click="handleAdd">新增用户</el-button>
        </div>
      </template>
      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="realName" label="姓名" min-width="100" />
        <el-table-column prop="phone" label="电话" min-width="130" />
        <el-table-column prop="role" label="角色" min-width="100">
          <template #default="scope">
            <el-tag :type="getRoleType(scope.row.role)">{{ getRoleName(scope.row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="160">
          <template #default="scope">{{ formatTime(scope.row.createTime) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="scope">
            <el-button size="small" link @click="handleEdit(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" link @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="form" :rules="rules" ref="userForm" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" :disabled="!!editId" />
        </el-form-item>
        <el-form-item label="密码" :prop="editId ? '' : 'password'">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" />
          <div v-if="editId" style="color: #909399; font-size: 12px;">留空则不修改密码</div>
        </el-form-item>
        <el-form-item label="姓名" prop="realName">
          <el-input v-model="form.realName" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入电话" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="管理员" value="ADMIN" />
            <el-option label="房东" value="LANDLORD" />
            <el-option label="租户" value="TENANT" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { getUsers, createUser, updateUser, deleteUser } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'AdminUsers',
  data() {
    return {
      users: [],
      loading: false,
      dialogVisible: false,
      dialogTitle: '新增用户',
      editId: null,
      form: { username: '', password: '', realName: '', phone: '', role: 'TENANT' },
      rules: {
        username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
        password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
        realName: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
        role: [{ required: true, message: '请选择角色', trigger: 'change' }]
      }
    }
  },
  created() { this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try { 
        const res = await getUsers()
        this.users = res.data
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    handleAdd() {
      this.editId = null
      this.dialogTitle = '新增用户'
      this.form = { username: '', password: '', realName: '', phone: '', role: 'TENANT' }
      this.dialogVisible = true
    },
    handleEdit(row) {
      this.editId = row.id
      this.dialogTitle = '编辑用户'
      this.form = { username: row.username, password: '', realName: row.realName, phone: row.phone, role: row.role }
      this.dialogVisible = true
    },
    handleDelete(row) {
      ElMessageBox.confirm('确定要删除该用户吗？', '提示', { type: 'warning' }).then(async () => {
        await deleteUser(row.id)
        ElMessage.success('删除成功')
        this.loadData()
      }).catch(() => {})
    },
    handleSubmit() {
      this.$refs.userForm.validate(async (valid) => {
        if (valid) {
          try {
            if (this.editId) {
              const updateData = { ...this.form }
              if (!updateData.password) delete updateData.password
              await updateUser(this.editId, updateData)
              ElMessage.success('更新成功')
            } else {
              await createUser(this.form)
              ElMessage.success('创建成功')
            }
            this.dialogVisible = false
            this.loadData()
          } catch (e) { console.error(e) }
        }
      })
    },
    getRoleType(role) {
      const types = { ADMIN: 'danger', LANDLORD: 'warning', TENANT: 'success' }
      return types[role] || ''
    },
    getRoleName(role) {
      const names = { ADMIN: '管理员', LANDLORD: '房东', TENANT: '租户' }
      return names[role] || role
    },
    formatTime(time) {
      if (!time) return '-'
      const date = new Date(time)
      const y = date.getFullYear()
      const m = String(date.getMonth() + 1).padStart(2, '0')
      const d = String(date.getDate()).padStart(2, '0')
      const h = String(date.getHours()).padStart(2, '0')
      const min = String(date.getMinutes()).padStart(2, '0')
      return `${y}-${m}-${d} ${h}:${min}`
    }
  }
}
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
