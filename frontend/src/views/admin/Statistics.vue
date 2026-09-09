<template>
  <div class="statistics">
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <el-icon><User /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.totalUsers || 0 }}</div>
            <div class="stat-label">用户总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <el-icon><House /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.totalApartments || 0 }}</div>
            <div class="stat-label">房源总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.totalContracts || 0 }}</div>
            <div class="stat-label">合同总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.occupancyRate || 0 }}%</div>
            <div class="stat-label">整体出租率</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card small">
          <div class="stat-info">
            <div class="stat-value text-warning">{{ statistics.pendingAudit || 0 }}</div>
            <div class="stat-label">待审核房源</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card small">
          <div class="stat-info">
            <div class="stat-value text-danger">{{ statistics.pendingComplaints || 0 }}</div>
            <div class="stat-label">待处理投诉</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card small">
          <div class="stat-info">
            <div class="stat-value text-info">{{ statistics.landlordCount || 0 }}</div>
            <div class="stat-label">房东数量</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card small">
          <div class="stat-info">
            <div class="stat-value text-success">{{ statistics.tenantCount || 0 }}</div>
            <div class="stat-label">租客数量</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header><span>用户增长趋势（近6个月）</span></template>
          <div ref="userChartRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span>房源状态分布</span></template>
          <div ref="apartmentChartRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header><span>收入统计（近6个月）</span></template>
          <div ref="incomeChartRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span>投诉建议统计</span></template>
          <div ref="complaintChartRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { getAdminStatistics } from '../../api'
import { User, House, Document, TrendCharts } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

export default {
  name: 'AdminStatistics',
  components: { User, House, Document, TrendCharts },
  data() {
    return {
      statistics: {},
      userChart: null,
      apartmentChart: null,
      incomeChart: null,
      complaintChart: null
    }
  },
  async created() {
    await this.loadData()
    this.$nextTick(() => {
      this.initCharts()
    })
  },
  methods: {
    async loadData() {
      try {
        const res = await getAdminStatistics()
        this.statistics = res.data || {}
      } catch (e) { console.error(e) }
    },
    initCharts() {
      this.initUserChart()
      this.initApartmentChart()
      this.initIncomeChart()
      this.initComplaintChart()
    },
    initUserChart() {
      this.userChart = echarts.init(this.$refs.userChartRef)
      const months = []
      const now = new Date()
      for (let i = 5; i >= 0; i--) {
        const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
        months.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`)
      }
      let userData = months.map(() => 0)
      if (this.statistics.userGrowth) {
        this.statistics.userGrowth.forEach(item => {
          const idx = months.indexOf(item.month)
          if (idx !== -1) userData[idx] = item.count
        })
      }
      this.userChart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: months },
        yAxis: { type: 'value' },
        series: [{
          name: '新增用户',
          type: 'bar',
          data: userData,
          itemStyle: { color: '#667eea', borderRadius: [4, 4, 0, 0] }
        }]
      })
    },
    initApartmentChart() {
      this.apartmentChart = echarts.init(this.$refs.apartmentChartRef)
      const data = [
        { value: this.statistics.rentedApartments || 0, name: '已出租', itemStyle: { color: '#f5576c' } },
        { value: this.statistics.availableApartments || 0, name: '可出租', itemStyle: { color: '#43e97b' } },
        { value: this.statistics.pendingAudit || 0, name: '待审核', itemStyle: { color: '#4facfe' } }
      ]
      this.apartmentChart.setOption({
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        legend: { bottom: '5%', left: 'center' },
        series: [{
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
          label: { show: false, position: 'center' },
          emphasis: { label: { show: true, fontSize: '18', fontWeight: 'bold' } },
          labelLine: { show: false },
          data: data
        }]
      })
    },
    initIncomeChart() {
      this.incomeChart = echarts.init(this.$refs.incomeChartRef)
      const months = []
      const now = new Date()
      for (let i = 5; i >= 0; i--) {
        const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
        months.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`)
      }
      let incomeData = months.map(() => 0)
      if (this.statistics.monthlyIncomes) {
        this.statistics.monthlyIncomes.forEach(item => {
          const idx = months.indexOf(item.month)
          if (idx !== -1) incomeData[idx] = item.income
        })
      }
      this.incomeChart.setOption({
        tooltip: { trigger: 'axis', formatter: '{b}<br/>收入: ¥{c}' },
        xAxis: { type: 'category', data: months },
        yAxis: { type: 'value', axisLabel: { formatter: '¥{value}' } },
        series: [{
          name: '收入',
          type: 'line',
          smooth: true,
          data: incomeData,
          areaStyle: { color: 'rgba(67, 233, 123, 0.3)' },
          lineStyle: { color: '#43e97b' },
          itemStyle: { color: '#43e97b' }
        }]
      })
    },
    initComplaintChart() {
      this.complaintChart = echarts.init(this.$refs.complaintChartRef)
      const data = [
        { value: this.statistics.pendingComplaints || 0, name: '待处理', itemStyle: { color: '#f5576c' } },
        { value: this.statistics.processedComplaints || 0, name: '已处理', itemStyle: { color: '#43e97b' } }
      ]
      this.complaintChart.setOption({
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        legend: { bottom: '5%', left: 'center' },
        series: [{
          type: 'pie',
          radius: '60%',
          data: data,
          emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
        }]
      })
    },
    formatMoney(val) {
      if (val >= 10000) return (val / 10000).toFixed(1) + '万'
      return val.toLocaleString()
    }
  },
  beforeUnmount() {
    if (this.userChart) this.userChart.dispose()
    if (this.apartmentChart) this.apartmentChart.dispose()
    if (this.incomeChart) this.incomeChart.dispose()
    if (this.complaintChart) this.complaintChart.dispose()
  }
}
</script>

<style scoped>
.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
}
.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 20px;
}
.stat-card.small :deep(.el-card__body) {
  justify-content: center;
  padding: 15px;
}
.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
}
.stat-icon .el-icon {
  font-size: 28px;
  color: white;
}
.stat-info {
  flex: 1;
}
.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}
.stat-value.text-warning { color: #e6a23c; }
.stat-value.text-danger { color: #f56c6c; }
.stat-value.text-info { color: #909399; }
.stat-value.text-success { color: #67c23a; }
.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}
</style>
