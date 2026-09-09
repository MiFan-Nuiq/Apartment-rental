<template>
  <div class="statistics">
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
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
          <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <el-icon><Key /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.rentedApartments || 0 }}</div>
            <div class="stat-label">已出租</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.rentalRate || 0 }}%</div>
            <div class="stat-label">出租率</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
            <el-icon><Money /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">¥{{ formatMoney(statistics.totalIncome || 0) }}</div>
            <div class="stat-label">总收入</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header><span>收入趋势（近6个月）</span></template>
          <div ref="incomeChartRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span>房源状态分布</span></template>
          <div ref="statusChartRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header><span>待处理事项</span></template>
          <el-table :data="pendingItems" stripe>
            <el-table-column prop="type" label="类型" min-width="100">
              <template #default="scope">
                <el-tag :type="scope.row.typeTag">{{ scope.row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="content" label="内容" min-width="200" show-overflow-tooltip />
            <el-table-column prop="time" label="时间" min-width="140" />
            <el-table-column label="操作" min-width="100">
              <template #default="scope">
                <el-button type="primary" size="small" @click="handlePending(scope.row)">处理</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="pendingItems.length === 0" description="暂无待处理事项" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span>最新评价</span></template>
          <el-table :data="recentReviews" stripe>
            <el-table-column label="房源" min-width="120">
              <template #default="scope">{{ scope.row.apartment?.name }}</template>
            </el-table-column>
            <el-table-column label="评分" min-width="120">
              <template #default="scope">
                <el-rate v-model="scope.row.rating" disabled />
              </template>
            </el-table-column>
            <el-table-column prop="content" label="内容" min-width="180" show-overflow-tooltip />
            <el-table-column label="时间" min-width="100">
              <template #default="scope">{{ formatDate(scope.row.createTime) }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-if="recentReviews.length === 0" description="暂无评价" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { getLandlordStatistics, getAppointmentsByLandlord, getRepairsByLandlord } from '../../api'
import { House, Key, TrendCharts, Money } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

export default {
  name: 'LandlordStatistics',
  components: { House, Key, TrendCharts, Money },
  data() {
    return {
      statistics: {},
      pendingItems: [],
      recentReviews: [],
      incomeChart: null,
      statusChart: null
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
        const userId = localStorage.getItem('userId')
        const [statRes, aptRes, repairRes] = await Promise.all([
          getLandlordStatistics(userId),
          getAppointmentsByLandlord(userId),
          getRepairsByLandlord(userId)
        ])
        this.statistics = statRes.data || {}
        const pendingAppointments = aptRes.data.filter(a => a.status === '待处理').map(a => ({
          type: '预约看房',
          typeTag: 'primary',
          content: `${a.tenant?.realName || a.tenant?.username} 预约 ${a.apartment?.name}`,
          time: this.formatTime(a.createTime),
          route: '/landlord/appointments'
        }))
        const pendingRepairs = repairRes.data.filter(r => r.status === '待处理').map(r => ({
          type: '维修申请',
          typeTag: 'warning',
          content: `${r.apartment?.name}: ${r.description}`,
          time: this.formatTime(r.createTime),
          route: '/landlord/repairs'
        }))
        this.pendingItems = [...pendingAppointments, ...pendingRepairs].slice(0, 5)
        this.recentReviews = this.statistics.recentReviews || []
      } catch (e) { console.error(e) }
    },
    initCharts() {
      this.initIncomeChart()
      this.initStatusChart()
    },
    initIncomeChart() {
      this.incomeChart = echarts.init(this.$refs.incomeChartRef)
      const months = []
      const incomes = []
      const now = new Date()
      for (let i = 5; i >= 0; i--) {
        const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
        months.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`)
        incomes.push(0)
      }
      if (this.statistics.monthlyIncomes) {
        this.statistics.monthlyIncomes.forEach(item => {
          const idx = months.indexOf(item.month)
          if (idx !== -1) incomes[idx] = item.income
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
          data: incomes,
          areaStyle: { color: 'rgba(102, 126, 234, 0.3)' },
          lineStyle: { color: '#667eea' },
          itemStyle: { color: '#667eea' }
        }]
      })
    },
    initStatusChart() {
      this.statusChart = echarts.init(this.$refs.statusChartRef)
      const data = [
        { value: this.statistics.rentedApartments || 0, name: '已出租', itemStyle: { color: '#f5576c' } },
        { value: this.statistics.vacantApartments || 0, name: '空置', itemStyle: { color: '#4facfe' } }
      ]
      this.statusChart.setOption({
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
    handlePending(row) {
      this.$router.push(row.route)
    },
    formatMoney(val) {
      if (val >= 10000) return (val / 10000).toFixed(1) + '万'
      return val.toLocaleString()
    },
    formatDate(date) {
      if (!date) return '-'
      const d = new Date(date)
      return `${d.getMonth() + 1}/${d.getDate()}`
    },
    formatTime(time) {
      if (!time) return '-'
      const date = new Date(time)
      return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
    }
  },
  beforeUnmount() {
    if (this.incomeChart) this.incomeChart.dispose()
    if (this.statusChart) this.statusChart.dispose()
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
.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}
</style>
