<template>
  <div class="favorites">
    <el-card>
      <template #header><span>我的收藏</span></template>
      <el-table :data="favorites" v-loading="loading" stripe>
        <el-table-column label="房源" min-width="180">
          <template #default="scope">
            <div style="display: flex; align-items: center; gap: 12px;">
              <el-image v-if="scope.row.apartment?.coverImage" :src="getImageUrl(scope.row.apartment.coverImage)" style="width: 60px; height: 60px; border-radius: 6px;" fit="cover" />
              <div>
                <div style="font-weight: 500;">{{ scope.row.apartment?.name }}</div>
                <div style="color: #909399; font-size: 12px;">{{ scope.row.apartment?.address }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="月租" min-width="100">
          <template #default="scope">¥{{ formatMoney(scope.row.apartment?.monthlyRent) }}</template>
        </el-table-column>
        <el-table-column label="状态" min-width="80">
          <template #default="scope">
            <el-tag :type="scope.row.apartment?.status === '空置' ? 'success' : 'info'">{{ scope.row.apartment?.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="收藏时间" min-width="140">
          <template #default="scope">{{ formatTime(scope.row.createTime) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="scope">
            <el-button size="small" link @click="viewApartment(scope.row.apartment)">查看</el-button>
            <el-button size="small" type="danger" link @click="handleRemove(scope.row)">取消收藏</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && favorites.length === 0" description="暂无收藏" />
    </el-card>

    <el-dialog v-model="viewDialogVisible" title="房源详情" width="600px">
      <el-descriptions :column="2" border v-if="currentApartment">
        <el-descriptions-item label="公寓名称">{{ currentApartment.name }}</el-descriptions-item>
        <el-descriptions-item label="地址">{{ currentApartment.address }}</el-descriptions-item>
        <el-descriptions-item label="楼层">{{ currentApartment.floor || '-' }}层</el-descriptions-item>
        <el-descriptions-item label="面积">{{ currentApartment.area || '-' }} ㎡</el-descriptions-item>
        <el-descriptions-item label="月租">¥{{ formatMoney(currentApartment.monthlyRent) }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="currentApartment.status === '空置' ? 'success' : 'info'">{{ currentApartment.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ currentApartment.description || '暂无描述' }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="viewDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleAppointment" v-if="currentApartment?.status === '空置'">预约看房</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { getFavorites, removeFavorite } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'TenantFavorites',
  data() {
    return {
      favorites: [],
      loading: false,
      viewDialogVisible: false,
      currentApartment: null
    }
  },
  created() { this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const userId = localStorage.getItem('userId')
        const res = await getFavorites(userId)
        this.favorites = res.data
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    viewApartment(apartment) {
      this.currentApartment = apartment
      this.viewDialogVisible = true
    },
    handleRemove(row) {
      ElMessageBox.confirm('确定要取消收藏吗？', '提示', { type: 'warning' }).then(async () => {
        const userId = localStorage.getItem('userId')
        await removeFavorite(userId, row.apartment.id)
        ElMessage.success('已取消收藏')
        this.loadData()
      }).catch(() => {})
    },
    handleAppointment() {
      this.viewDialogVisible = false
      this.$router.push('/tenant/apartments')
    },
    getImageUrl(path) {
      if (!path) return ''
      if (path.startsWith('http')) return path
      return 'http://localhost:8080' + path
    },
    formatMoney(v) { return v ? parseFloat(v).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) : '-' },
    formatTime(time) {
      if (!time) return '-'
      const date = new Date(time)
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
    }
  }
}
</script>
