<template>
  <div class="appointments">
    <el-card>
      <template #header><span>看房预约</span></template>
      <el-table :data="appointments" v-loading="loading">
        <el-table-column label="公寓" width="150">
          <template #default="scope">{{ scope.row.apartment?.name || '-' }}</template>
        </el-table-column>
        <el-table-column label="租户ID" width="100">
          <template #default="scope">{{ scope.row.tenant?.id || '-' }}</template>
        </el-table-column>
        <el-table-column label="租户电话" width="130">
          <template #default="scope">{{ scope.row.tenant?.phone || '-' }}</template>
        </el-table-column>
        <el-table-column prop="appointmentTime" label="预约时间" width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="scope">
            <el-button size="small" type="success" @click="handleAccept(scope.row)" :disabled="scope.row.status !== '待处理'">接受</el-button>
            <el-button size="small" type="danger" @click="handleReject(scope.row)" :disabled="scope.row.status !== '待处理'">拒绝</el-button>
            <el-button size="small" type="warning" link @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { getAppointmentsByLandlord, handleAppointment, deleteAppointment } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'LandlordAppointments',
  data() { return { appointments: [], loading: false } },
  created() { this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const userId = localStorage.getItem('userId')
        this.appointments = (await getAppointmentsByLandlord(userId)).data
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    handleAccept(row) {
      ElMessageBox.prompt('请输入回复信息', '接受预约', { confirmButtonText: '确定', cancelButtonText: '取消' }).then(async ({ value }) => {
        await handleAppointment(row.id, '已接受', value || '')
        ElMessage.success('已接受预约')
        this.loadData()
      }).catch(() => {})
    },
    handleReject(row) {
      ElMessageBox.prompt('请输入拒绝原因', '拒绝预约', { confirmButtonText: '确定', cancelButtonText: '取消' }).then(async ({ value }) => {
        await handleAppointment(row.id, '已拒绝', value || '')
        ElMessage.success('已拒绝预约')
        this.loadData()
      }).catch(() => {})
    },
    handleDelete(row) {
      ElMessageBox.confirm('确定要删除该预约记录吗？', '提示', { type: 'warning' }).then(async () => {
        await deleteAppointment(row.id)
        ElMessage.success('删除成功')
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
