<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #409EFF"><el-icon size="30"><User /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.users }}</div>
              <div class="stat-label">用户总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #67C23A"><el-icon size="30"><House /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.apartments }}</div>
              <div class="stat-label">公寓总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #E6A23C"><el-icon size="30"><Document /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.contracts }}</div>
              <div class="stat-label">合同总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #F56C6C"><el-icon size="30"><Money /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ formatMoney(stats.income) }}</div>
              <div class="stat-label">总收入(元)</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { User, House, Document, Money } from '@element-plus/icons-vue'
import { getUsers, getApartments, getContracts, getPayments } from '../../api'

export default {
  name: 'AdminDashboard',
  components: { User, House, Document, Money },
  data() {
    return { stats: { users: 0, apartments: 0, contracts: 0, income: 0 } }
  },
  created() { this.loadData() },
  methods: {
    async loadData() {
      try {
        const [users, apartments, contracts, payments] = await Promise.all([getUsers(), getApartments(), getContracts(), getPayments()])
        this.stats.users = users.data.length
        this.stats.apartments = apartments.data.length
        this.stats.contracts = contracts.data.length
        this.stats.income = payments.data.filter(p => p.status === '已支付').reduce((sum, p) => sum + parseFloat(p.amount || 0), 0)
      } catch (e) { console.error(e) }
    },
    formatMoney(v) { return v ? parseFloat(v).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) : '0.00' }
  }
}
</script>

<style scoped>
.dashboard { padding: 0; }
.stat-card { height: 120px; }
.stat-content { display: flex; align-items: center; gap: 20px; }
.stat-icon { width: 60px; height: 60px; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; }
.stat-value { font-size: 28px; font-weight: bold; color: #333; }
.stat-label { font-size: 14px; color: #999; margin-top: 5px; }
</style>
