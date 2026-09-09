<template>
  <div class="repairs">
    <el-card>
      <template #header><span>报障处理</span></template>
      <el-table :data="repairs" v-loading="loading">
        <el-table-column label="公寓" width="150">
          <template #default="scope">{{ scope.row.apartment?.name || '-' }}</template>
        </el-table-column>
        <el-table-column label="租户" width="100">
          <template #default="scope">{{ scope.row.tenant?.realName || '-' }}</template>
        </el-table-column>
        <el-table-column prop="title" label="报障标题" width="150" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" @click="handleRepair(scope.row)" :disabled="scope.row.status !== '待处理'">处理</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { getRepairsByLandlord, handleRepair } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'LandlordRepairs',
  data() { return { repairs: [], loading: false } },
  created() { this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const userId = localStorage.getItem('userId')
        this.repairs = (await getRepairsByLandlord(userId)).data
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    handleRepair(row) {
      ElMessageBox.prompt('请输入处理结果', '处理报障', { confirmButtonText: '确定', cancelButtonText: '取消' }).then(async ({ value }) => {
        await handleRepair(row.id, '已处理', value || '')
        ElMessage.success('处理成功')
        this.loadData()
      }).catch(() => {})
    },
    getStatusType(s) { return { '待处理': 'warning', '处理中': 'primary', '已处理': 'success' }[s] || '' }
  }
}
</script>
