<template>
  <div class="apartments">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>房源列表</span>
        </div>
      </template>
      <div class="filter-bar">
        <el-input v-model="searchKeyword" placeholder="搜索公寓名称或地址" clearable style="width: 250px" @clear="loadData" @keyup.enter="loadData">
          <template #append>
            <el-button icon="Search" @click="loadData" />
          </template>
        </el-input>
      </div>
      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="8" v-for="apt in filteredApartments" :key="apt.id">
          <el-card shadow="hover" class="apartment-card" :body-style="{ padding: '0' }">
            <div class="cover-wrapper" @click="showDetail(apt)">
              <el-image v-if="apt.coverImage" :src="apt.coverImage" style="width: 100%; height: 180px;" fit="cover" />
              <div v-else class="no-cover">
                <el-icon style="font-size: 40px; color: #c0c4cc;"><Picture /></el-icon>
                <span>暂无封面</span>
              </div>
              <div class="status-overlay" v-if="apt.status === '已出租'">
                <el-tag type="info" effect="dark">已出租</el-tag>
              </div>
              <div class="favorite-btn" @click.stop="toggleFavorite(apt)">
                <el-icon :class="{ 'is-favorite': apt.isFavorited }">
                  <StarFilled v-if="apt.isFavorited" />
                  <Star v-else />
                </el-icon>
              </div>
              <div class="rating-badge" v-if="apt.avgRating">
                <el-icon><StarFilled /></el-icon>
                {{ apt.avgRating.toFixed(1) }}
              </div>
            </div>
            <div class="apartment-info">
              <h3>{{ apt.name }}</h3>
              <p class="address"><el-icon><Location /></el-icon> {{ apt.address }}</p>
              <p class="detail">
                <span>{{ apt.floor || '-' }}层</span>
                <span>{{ apt.area || '-' }}㎡</span>
              </p>
              <div class="price-row">
                <span class="rent">月租: <span class="price">¥{{ formatMoney(apt.monthlyRent) }}</span></span>
                <el-tag :type="apt.status === '空置' ? 'success' : 'info'" size="small">{{ apt.status }}</el-tag>
              </div>
              <div class="apartment-actions">
                <el-button type="primary" size="small" @click="showDetail(apt)">查看详情</el-button>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      <el-empty v-if="filteredApartments.length === 0" description="暂无房源" />
    </el-card>

    <el-dialog v-model="dialogVisible" title="预约看房" width="500px">
      <el-form :model="form" :rules="rules" ref="aptForm" label-width="80px">
        <el-form-item label="公寓">
          <el-input :value="selectedApartment?.name" disabled />
        </el-form-item>
        <el-form-item label="预约时间" prop="appointmentTime">
          <el-date-picker v-model="form.appointmentTime" type="datetime" placeholder="选择预约时间" style="width: 100%" value-format="YYYY-MM-DD HH:mm:ss" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">提交预约</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailDialogVisible" :title="currentApartment?.name" width="900px">
      <div class="detail-content">
        <div class="detail-images" v-if="detailImages.length > 0">
          <el-carousel :interval="4000" height="300px" indicator-position="outside">
            <el-carousel-item v-for="(img, index) in detailImages" :key="index">
              <el-image :src="img" style="width: 100%; height: 300px;" fit="cover" :preview-src-list="detailImages" />
            </el-carousel-item>
          </el-carousel>
        </div>
        <div v-else class="no-detail-images">
          <el-image v-if="currentApartment?.coverImage" :src="currentApartment.coverImage" style="width: 100%; height: 300px;" fit="cover" />
          <div v-else style="display: flex; align-items: center; justify-content: center; height: 300px; background: #f5f7fa; color: #909399;">暂无图片</div>
        </div>
        <el-descriptions :column="2" border style="margin-top: 20px;">
          <el-descriptions-item label="地址">{{ currentApartment?.address }}</el-descriptions-item>
          <el-descriptions-item label="楼层">{{ currentApartment?.floor || '-' }}层</el-descriptions-item>
          <el-descriptions-item label="面积">{{ currentApartment?.area || '-' }} ㎡</el-descriptions-item>
          <el-descriptions-item label="月租">
            <span style="color: #f56c6c; font-size: 18px; font-weight: bold;">¥{{ formatMoney(currentApartment?.monthlyRent) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentApartment?.status === '空置' ? 'success' : 'info'">{{ currentApartment?.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="房东">{{ currentApartment?.landlord?.realName || '-' }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ currentApartment?.landlord?.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ currentApartment?.description || '暂无描述' }}</el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">已出租时间段</el-divider>
        <div v-if="apartmentContracts.length > 0" class="rented-periods">
          <el-timeline>
            <el-timeline-item v-for="contract in apartmentContracts" :key="contract.id" :type="getContractTimelineType(contract)" placement="top">
              <el-card shadow="hover" style="padding: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <div>
                    <span style="font-weight: bold;">{{ contract.startDate }} 至 {{ contract.endDate }}</span>
                    <el-tag :type="getContractStatusType(contract.status)" size="small" style="margin-left: 10px;">{{ contract.status }}</el-tag>
                    <el-tag v-if="contract.contractType === '续租'" type="warning" size="small" style="margin-left: 5px;">续租</el-tag>
                  </div>
                </div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </div>
        <el-empty v-else description="暂无出租记录" :image-size="60" />

        <el-divider content-position="left">
          <span>租客评价</span>
          <span v-if="apartmentReviews.length > 0" style="margin-left: 10px; color: #f59e0b;">
            <el-icon><StarFilled /></el-icon>
            {{ averageRating.toFixed(1) }}分 ({{ apartmentReviews.length }}条评价)
          </span>
        </el-divider>
        <div v-if="apartmentReviews.length > 0" class="reviews-section">
          <div v-for="review in apartmentReviews" :key="review.id" class="review-item">
            <div class="review-header">
              <div class="reviewer-info">
                <span class="reviewer-name">{{ review.tenant?.realName || '匿名用户' }}</span>
                <el-rate v-model="review.rating" disabled size="small" />
              </div>
              <span class="review-time">{{ formatTime(review.createTime) }}</span>
            </div>
            <div class="review-content">{{ review.content }}</div>
            <div v-if="review.landlordReply" class="landlord-reply">
              <span class="reply-label">房东回复：</span>{{ review.landlordReply }}
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无评价" :image-size="60" />

        <el-alert v-if="currentApartment?.status === '已出租'" type="info" style="margin-top: 15px;" :closable="false">
          <template #title>
            <span>该房源当前已出租，您可以查看已出租时间段。如需租房，请选择其他时间段或联系房东咨询。</span>
          </template>
        </el-alert>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button :type="currentApartment?.isFavorited ? 'warning' : 'default'" @click="toggleFavorite(currentApartment)">
          {{ currentApartment?.isFavorited ? '取消收藏' : '收藏房源' }}
        </el-button>
        <el-button type="primary" @click="handleAppointment(currentApartment)">预约看房</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { getAuditedApartments, createAppointment, getContractsByApartment, checkFavorite, addFavorite, removeFavorite, getApprovedApartmentReviews } from '../../api'
import { ElMessage } from 'element-plus'
import { Location, Picture, Star, StarFilled } from '@element-plus/icons-vue'

export default {
  name: 'TenantApartments',
  components: { Location, Picture, Star, StarFilled },
  data() {
    return {
      apartments: [],
      loading: false,
      searchKeyword: '',
      dialogVisible: false,
      detailDialogVisible: false,
      selectedApartment: null,
      currentApartment: null,
      apartmentContracts: [],
      apartmentReviews: [],
      form: { appointmentTime: '', remark: '' },
      rules: { appointmentTime: [{ required: true, message: '请选择预约时间', trigger: 'change' }] }
    }
  },
  computed: {
    filteredApartments() {
      let result = this.apartments
      if (this.searchKeyword) {
        const keyword = this.searchKeyword.toLowerCase()
        result = result.filter(a => a.name?.toLowerCase().includes(keyword) || a.address?.toLowerCase().includes(keyword))
      }
      return result
    },
    detailImages() {
      if (!this.currentApartment?.detailImages) return []
      return this.currentApartment.detailImages.split(',').filter(img => img)
    },
    averageRating() {
      if (this.apartmentReviews.length === 0) return 0
      const sum = this.apartmentReviews.reduce((acc, r) => acc + r.rating, 0)
      return sum / this.apartmentReviews.length
    }
  },
  created() { this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const userId = localStorage.getItem('userId')
        const res = await getAuditedApartments()
        this.apartments = res.data
        for (const apt of this.apartments) {
          try {
            const favRes = await checkFavorite(userId, apt.id)
            apt.isFavorited = favRes.data
            const revRes = await getApprovedApartmentReviews(apt.id)
            const reviews = revRes.data || []
            if (reviews.length > 0) {
              const sum = reviews.reduce((acc, r) => acc + r.rating, 0)
              apt.avgRating = sum / reviews.length
            }
          } catch (e) {
            apt.isFavorited = false
            apt.avgRating = null
          }
        }
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    async toggleFavorite(apt) {
      const userId = localStorage.getItem('userId')
      try {
        if (apt.isFavorited) {
          await removeFavorite(userId, apt.id)
          ElMessage.success('已取消收藏')
        } else {
          await addFavorite({ tenantId: userId, apartmentId: apt.id })
          ElMessage.success('收藏成功')
        }
        apt.isFavorited = !apt.isFavorited
      } catch (e) {
        console.error(e)
        ElMessage.error('操作失败')
      }
    },
    async showDetail(apt) {
      this.currentApartment = apt
      this.detailDialogVisible = true
      try {
        const [conRes, revRes] = await Promise.all([
          getContractsByApartment(apt.id),
          getApprovedApartmentReviews(apt.id)
        ])
        this.apartmentContracts = conRes.data.filter(c => c.status === '生效中' || c.status === '待确认')
        this.apartmentReviews = revRes.data || []
      } catch (e) { console.error(e) }
    },
    handleAppointment(apt) {
      this.selectedApartment = apt
      this.form = { appointmentTime: '', remark: '' }
      this.detailDialogVisible = false
      this.dialogVisible = true
    },
    handleSubmit() {
      this.$refs.aptForm.validate(async (valid) => {
        if (valid) {
          try {
            const userId = localStorage.getItem('userId')
            await createAppointment({
              apartment: { id: this.selectedApartment.id },
              tenant: { id: userId },
              landlord: { id: this.selectedApartment.landlord?.id },
              appointmentTime: this.form.appointmentTime,
              remark: this.form.remark
            })
            ElMessage.success('预约成功')
            this.dialogVisible = false
          } catch (e) { console.error(e) }
        }
      })
    },
    formatMoney(v) { return v ? parseFloat(v).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) : '-' },
    getContractStatusType(s) { return { '待确认': 'info', '生效中': 'success', '已到期': 'warning', '已终止': 'danger' }[s] || '' },
    getContractTimelineType(contract) {
      if (contract.status === '生效中') return 'success'
      if (contract.status === '待确认') return 'warning'
      return 'primary'
    },
    formatTime(time) {
      if (!time) return '-'
      const date = new Date(time)
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    }
  }
}
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.filter-bar { display: flex; align-items: center; }
.apartment-card { margin-bottom: 20px; cursor: pointer; transition: transform 0.2s; }
.apartment-card:hover { transform: translateY(-5px); }
.cover-wrapper { width: 100%; height: 180px; overflow: hidden; position: relative; }
.no-cover { width: 100%; height: 180px; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #f5f7fa; color: #909399; }
.status-overlay { position: absolute; top: 10px; right: 10px; }
.favorite-btn {
  position: absolute;
  top: 10px;
  left: 10px;
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
.favorite-btn:hover { background: #fff; transform: scale(1.1); }
.favorite-btn .el-icon { font-size: 20px; color: #c0c4cc; transition: all 0.3s; }
.favorite-btn .el-icon.is-favorite { color: #f59e0b; }
.rating-badge {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.7);
  color: #f59e0b;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.apartment-info { padding: 15px; }
.apartment-info h3 { margin: 0 0 10px 0; color: #303133; font-size: 16px; }
.apartment-info .address { color: #909399; font-size: 13px; margin: 5px 0; display: flex; align-items: center; }
.apartment-info .address .el-icon { margin-right: 4px; }
.apartment-info .detail { color: #606266; font-size: 13px; margin: 8px 0; }
.apartment-info .detail span { margin-right: 15px; }
.price-row { display: flex; justify-content: space-between; align-items: center; margin: 10px 0; }
.apartment-info .rent { font-size: 13px; }
.apartment-info .price { color: #f56c6c; font-size: 18px; font-weight: bold; }
.apartment-actions { margin-top: 10px; text-align: right; }
.detail-content { padding: 10px 0; }
.no-detail-images { width: 100%; }
.rented-periods { margin-top: 10px; max-height: 300px; overflow-y: auto; }
.reviews-section { max-height: 400px; overflow-y: auto; }
.review-item { padding: 15px; border-bottom: 1px solid #ebeef5; }
.review-item:last-child { border-bottom: none; }
.review-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.reviewer-info { display: flex; align-items: center; gap: 10px; }
.reviewer-name { font-weight: 500; color: #303133; }
.review-time { color: #909399; font-size: 12px; }
.review-content { color: #606266; line-height: 1.6; }
.landlord-reply { margin-top: 10px; padding: 10px; background: #f5f7fa; border-radius: 4px; font-size: 13px; color: #606266; }
.reply-label { color: #409eff; font-weight: 500; }
</style>
