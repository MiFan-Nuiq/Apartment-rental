<template>
  <div class="repairs">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>报障申请</span>
          <el-button type="primary" @click="handleAdd">提交报障</el-button>
        </div>
      </template>
      <el-table :data="repairs" v-loading="loading">
        <el-table-column prop="title" label="报障标题" width="150" />
        <el-table-column label="公寓" width="150">
          <template #default="scope">{{ scope.row.apartment?.name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reply" label="回复" width="200" />
        <el-table-column prop="createTime" label="提交时间" width="180" />
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="提交报障" width="500px">
      <el-form :model="form" :rules="rules" ref="repairForm" label-width="80px">
        <el-form-item label="合同" prop="contractId">
          <el-select v-model="form.contractId" placeholder="请选择合同" style="width: 100%" @change="handleContractChange">
            <el-option v-for="item in activeContracts" :key="item.id" :label="item.contractNo" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入报障标题" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入报障描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { getRepairsByTenant, createRepair, getContractsByTenant } from '../../api'
import { ElMessage } from 'element-plus'

export default {
  name: 'TenantRepairs',
  data() {
    return {
      repairs: [],
      contracts: [],
      loading: false,
      dialogVisible: false,
      form: { contractId: null, title: '', description: '' },
      rules: {
        contractId: [{ required: true, message: '请选择合同', trigger: 'change' }],
        title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
        description: [{ required: true, message: '请输入描述', trigger: 'blur' }]
      }
    }
  },
  computed: {
    activeContracts() { return this.contracts.filter(c => c.status === '生效中') }
  },
  created() { this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const userId = localStorage.getItem('userId')
        const [repairs, contracts] = await Promise.all([getRepairsByTenant(userId), getContractsByTenant(userId)])
        this.repairs = repairs.data
        this.contracts = contracts.data
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    handleAdd() {
      this.form = { contractId: null, title: '', description: '' }
      this.dialogVisible = true
    },
    handleContractChange(contractId) {
      const contract = this.contracts.find(c => c.id === contractId)
      if (contract) {
        this.form.apartmentId = contract.apartment?.id
        this.form.landlordId = contract.landlord?.id
      }
    },
    handleSubmit() {
      this.$refs.repairForm.validate(async (valid) => {
        if (valid) {
          try {
            const userId = localStorage.getItem('userId')
            const contract = this.contracts.find(c => c.id === this.form.contractId)
            await createRepair({
              apartment: { id: contract.apartment?.id },
              contract: { id: this.form.contractId },
              tenant: { id: userId },
              landlord: { id: contract.landlord?.id },
              title: this.form.title,
              description: this.form.description
            })
            ElMessage.success('提交成功')
            this.dialogVisible = false
            this.loadData()
          } catch (e) { console.error(e) }
        }
      })
    },
    getStatusType(s) { return { '待处理': 'warning', '处理中': 'primary', '已处理': 'success' }[s] || '' }
  }
}
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
