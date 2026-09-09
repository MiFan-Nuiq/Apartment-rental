<template>
  <div class="contracts">
    <el-card>
      <template #header><span>合同管理</span></template>
      <el-table :data="contracts" v-loading="loading">
        <el-table-column prop="contractNo" label="合同编号" width="150" />
        <el-table-column label="公寓" width="150">
          <template #default="scope">{{ scope.row.apartment?.name || '-' }}</template>
        </el-table-column>
        <el-table-column label="租户" width="100">
          <template #default="scope">{{ scope.row.tenant?.realName || '-' }}</template>
        </el-table-column>
        <el-table-column label="房东" width="100">
          <template #default="scope">{{ scope.row.landlord?.realName || '-' }}</template>
        </el-table-column>
        <el-table-column prop="startDate" label="开始日期" width="120" />
        <el-table-column prop="endDate" label="结束日期" width="120" />
        <el-table-column prop="monthlyRent" label="月租(元)" width="100">
          <template #default="scope">{{ formatMoney(scope.row.monthlyRent) }}</template>
        </el-table-column>
        <el-table-column prop="contractType" label="类型" width="80">
          <template #default="scope">
            <el-tag :type="scope.row.contractType === '续租' ? 'warning' : 'primary'" size="small">{{ scope.row.contractType }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" link @click="handleView(scope.row)">查看</el-button>
            <el-button size="small" type="danger" link @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="viewDialogVisible" title="合同详情" width="700px">
      <div class="contract-template" v-if="currentContract">
        <h2 style="text-align: center; margin-bottom: 20px;">房屋租赁合同</h2>
        <el-divider />
        <p><strong>合同编号：</strong>{{ currentContract.contractNo }}</p>
        <p><strong>合同类型：</strong>
          <el-tag :type="currentContract.contractType === '续租' ? 'warning' : 'primary'" size="small">{{ currentContract.contractType }}</el-tag>
        </p>
        <p v-if="currentContract.originalContractId"><strong>原合同ID：</strong>{{ currentContract.originalContractId }}</p>
        <p><strong>出租方（甲方）：</strong>{{ currentContract.landlord?.realName || '-' }}</p>
        <p><strong>承租方（乙方）：</strong>{{ currentContract.tenant?.realName || '-' }}</p>
        <p><strong>房屋地址：</strong>{{ currentContract.apartment?.address || '-' }} {{ currentContract.apartment?.name }}</p>
        <p><strong>房屋面积：</strong>{{ currentContract.apartment?.area || '-' }} 平方米</p>
        <el-divider />
        <h4>第一条 租赁期限</h4>
        <p>租赁期限自 <strong>{{ currentContract.startDate }}</strong> 起至 <strong>{{ currentContract.endDate }}</strong> 止。</p>
        <h4>第二条 租金及支付方式</h4>
        <p>每月租金为人民币 <strong>{{ formatMoney(currentContract.monthlyRent) }}</strong> 元。</p>
        <p>押金为人民币 <strong>{{ formatMoney(currentContract.deposit) }}</strong> 元。</p>
        <p>付款方式：<strong>{{ currentContract.paymentMethod }}</strong></p>
        <h4>第三条 甲方责任</h4>
        <p>1. 甲方应保证房屋及设施正常使用，负责房屋主体结构的维修。</p>
        <p>2. 甲方有权按约定收取租金和押金。</p>
        <h4>第四条 乙方责任</h4>
        <p>1. 乙方应按时缴纳租金及水电等费用。</p>
        <p>2. 乙方应爱护房屋设施，不得擅自改变房屋结构。</p>
        <p>3. 租赁期满或合同终止时，乙方应按时交还房屋。</p>
        <h4>第五条 违约责任</h4>
        <p>任何一方违反本合同约定，应向守约方支付相当于一个月租金的违约金。</p>
        <el-divider />
        <p><strong>合同状态：</strong><el-tag :type="getStatusType(currentContract.status)">{{ currentContract.status }}</el-tag></p>
        <p><strong>签订日期：</strong>{{ currentContract.createTime }}</p>
      </div>
      <template #footer>
        <el-button @click="viewDialogVisible = false">关闭</el-button>
        <el-button type="danger" @click="handleDelete(currentContract)">删除合同</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { getContracts, deleteContract } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'AdminContracts',
  data() {
    return {
      contracts: [],
      loading: false,
      viewDialogVisible: false,
      currentContract: null
    }
  },
  created() { this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try {
        this.contracts = (await getContracts()).data
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    handleView(contract) {
      this.currentContract = contract
      this.viewDialogVisible = true
    },
    handleDelete(contract) {
      ElMessageBox.confirm('确定要删除该合同吗？此操作不可恢复。', '警告', { 
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }).then(async () => {
        try {
          await deleteContract(contract.id)
          ElMessage.success('删除成功')
          this.viewDialogVisible = false
          this.loadData()
        } catch (e) {
          ElMessage.error(e.response?.data?.message || '删除失败')
        }
      }).catch(() => {})
    },
    formatMoney(v) { return v ? parseFloat(v).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) : '-' },
    getStatusType(s) { return { '待确认': 'info', '生效中': 'success', '已到期': 'warning', '已终止': 'danger' }[s] || '' }
  }
}
</script>

<style scoped>
.contract-template {
  padding: 20px;
  line-height: 1.8;
}
.contract-template h4 {
  margin-top: 15px;
  margin-bottom: 10px;
  color: #303133;
}
.contract-template p {
  text-indent: 2em;
  color: #606266;
}
</style>
