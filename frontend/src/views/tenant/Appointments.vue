<template>
  <div class="appointments">
    <el-card>
      <template #header><span>我的看房预约</span></template>
      <el-table :data="appointments" v-loading="loading">
        <el-table-column label="公寓" width="180">
          <template #default="scope">
            {{ scope.row.apartment?.name || '-' }}
            <el-tag type="info" size="small" style="margin-left: 5px;">ID:{{ scope.row.apartment?.id }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="房东" width="180">
          <template #default="scope">
            ID:{{ scope.row.landlord?.id }} ({{ scope.row.landlord?.realName || scope.row.landlord?.username || '-' }})
          </template>
        </el-table-column>
        <el-table-column label="房东电话" width="130">
          <template #default="scope">{{ scope.row.landlord?.phone || '-' }}</template>
        </el-table-column>
        <el-table-column prop="appointmentTime" label="预约时间" width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reply" label="房东回复" width="150">
          <template #default="scope">{{ scope.row.reply || '-' }}</template>
        </el-table-column>
        <el-table-column prop="remark" label="我的备注" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="scope">
            <el-button size="small" type="danger" link @click="handleDelete(scope.row)">取消</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { getAppointmentsByTenant, deleteAppointment } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'TenantAppointments',
  data() { return { appointments: [], loading: false } },
  created() { this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const userId = localStorage.getItem('userId')
        this.appointments = (await getAppointmentsByTenant(userId)).data
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    handleDelete(row) {
      ElMessageBox.confirm('确定要取消该预约吗？', '提示', { type: 'warning' }).then(async () => {
        await deleteAppointment(row.id)
        ElMessage.success('已取消预约')
        this.loadData()
      }).catch(() => {})
    },
    getStatusType(status) {
      const types = { '待处理': 'warning', '已接受': 'success', '已拒绝': 'danger' }
      return types[status] || ''
    }
  }
}
</script>
