<template>
  <div class="profile">
    <el-card>
      <template #header><span>个人中心</span></template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="用户ID">
          <el-tag type="primary" size="large">{{ user.id }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="用户名">{{ user.username }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ user.realName }}</el-descriptions-item>
        <el-descriptions-item label="电话">{{ user.phone }}</el-descriptions-item>
        <el-descriptions-item label="角色">
          <el-tag type="success">租户</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="注册时间">{{ user.createTime }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card style="margin-top: 20px;">
      <template #header><span>修改信息</span></template>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px" style="max-width: 500px;">
        <el-form-item label="姓名" prop="realName">
          <el-input v-model="form.realName" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入电话" />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="form.password" type="password" placeholder="留空则不修改" show-password />
        </el-form-item>
        <el-form-item label="确认密码" v-if="form.password">
          <el-input v-model="form.confirmPassword" type="password" placeholder="请确认新密码" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleUpdate">保存修改</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px;">
      <template #header><span>我的统计</span></template>
      <el-row :gutter="20">
        <el-col :span="6">
          <el-statistic title="待确认合同" :value="stats.pendingContracts" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="生效中合同" :value="stats.activeContracts" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="待支付账单" :value="stats.pendingPayments" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="待处理报修" :value="stats.pendingRepairs" />
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script>
import { getUser, updateUser } from '../../api'
import { ElMessage } from 'element-plus'

export default {
  name: 'TenantProfile',
  data() {
    return {
      user: {},
      form: { realName: '', phone: '', password: '', confirmPassword: '' },
      rules: {
        realName: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
        phone: [{ required: true, message: '请输入电话', trigger: 'blur' }]
      },
      stats: { pendingContracts: 0, activeContracts: 0, pendingPayments: 0, pendingRepairs: 0 }
    }
  },
  created() { this.loadData() },
  methods: {
    async loadData() {
      try {
        const userId = localStorage.getItem('userId')
        const res = await getUser(userId)
        this.user = res.data
        this.form.realName = this.user.realName
        this.form.phone = this.user.phone
        this.loadStats()
      } catch (e) { console.error(e) }
    },
    async loadStats() {
      try {
        const userId = localStorage.getItem('userId')
        const [contracts, payments, repairs] = await Promise.all([
          this.$axios.get(`/contracts/tenant/${userId}`),
          this.$axios.get(`/payments/tenant/${userId}`),
          this.$axios.get(`/repairs/tenant/${userId}`)
        ])
        this.stats.pendingContracts = contracts.data.data.filter(c => c.status === '待确认').length
        this.stats.activeContracts = contracts.data.data.filter(c => c.status === '生效中').length
        this.stats.pendingPayments = payments.data.data.filter(p => p.status === '待支付').length
        this.stats.pendingRepairs = repairs.data.data.filter(r => r.status === '待处理').length
      } catch (e) { console.error(e) }
    },
    async handleUpdate() {
      this.$refs.formRef.validate(async (valid) => {
        if (valid) {
          if (this.form.password && this.form.password !== this.form.confirmPassword) {
            ElMessage.error('两次输入的密码不一致')
            return
          }
          try {
            const userId = localStorage.getItem('userId')
            const updateData = { realName: this.form.realName, phone: this.form.phone }
            if (this.form.password) updateData.password = this.form.password
            await updateUser(userId, updateData)
            ElMessage.success('修改成功')
            this.loadData()
          } catch (e) { console.error(e) }
        }
      })
    }
  }
}
</script>
