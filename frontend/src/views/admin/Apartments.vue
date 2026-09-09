<template>
  <div class="apartments">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>房源审核</span>
        </div>
      </template>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="待审核" name="pending">
          <el-table :data="pendingApartments" v-loading="loading" stripe>
            <el-table-column label="封面" width="90">
              <template #default="scope">
                <el-image v-if="scope.row.coverImage" :src="scope.row.coverImage" style="width: 60px; height: 60px; border-radius: 6px;" fit="cover" :preview-src-list="[scope.row.coverImage]" />
                <span v-else style="color: #909399;">暂无</span>
              </template>
            </el-table-column>
            <el-table-column prop="name" label="公寓名称" min-width="140" />
            <el-table-column prop="address" label="地址" min-width="180" show-overflow-tooltip />
            <el-table-column prop="monthlyRent" label="月租(元)" min-width="100">
              <template #default="scope">{{ formatMoney(scope.row.monthlyRent) }}</template>
            </el-table-column>
            <el-table-column label="房东" min-width="100">
              <template #default="scope">
                <div>ID:{{ scope.row.landlord?.id }}</div>
                <div style="color: #909399; font-size: 12px;">{{ scope.row.landlord?.realName || '-' }}</div>
              </template>
            </el-table-column>
            <el-table-column label="提交时间" min-width="140">
              <template #default="scope">{{ formatTime(scope.row.createTime) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="scope">
                <el-button size="small" link @click="viewApartment(scope.row)">查看</el-button>
                <el-button size="small" type="success" link @click="handleAudit(scope.row, '审核通过')">通过</el-button>
                <el-button size="small" type="danger" link @click="showRejectDialog(scope.row)">拒绝</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="已审核" name="audited">
          <el-table :data="auditedApartments" v-loading="loading" stripe>
            <el-table-column label="封面" width="90">
              <template #default="scope">
                <el-image v-if="scope.row.coverImage" :src="scope.row.coverImage" style="width: 60px; height: 60px; border-radius: 6px;" fit="cover" :preview-src-list="[scope.row.coverImage]" />
                <span v-else style="color: #909399;">暂无</span>
              </template>
            </el-table-column>
            <el-table-column prop="name" label="公寓名称" min-width="140" />
            <el-table-column prop="address" label="地址" min-width="180" show-overflow-tooltip />
            <el-table-column prop="monthlyRent" label="月租(元)" min-width="100">
              <template #default="scope">{{ formatMoney(scope.row.monthlyRent) }}</template>
            </el-table-column>
            <el-table-column prop="auditStatus" label="审核状态" min-width="100">
              <template #default="scope">
                <el-tag :type="getAuditStatusType(scope.row.auditStatus)">{{ scope.row.auditStatus }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="房东" min-width="100">
              <template #default="scope">
                <div>ID:{{ scope.row.landlord?.id }}</div>
                <div style="color: #909399; font-size: 12px;">{{ scope.row.landlord?.realName || '-' }}</div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="scope">
                <el-button size="small" link @click="viewApartment(scope.row)">查看</el-button>
                <el-button size="small" type="danger" link @click="handleDelete(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="viewDialogVisible" title="房源详情" width="700px">
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
          <div v-else style="display: flex; align-items: center; justify-content: center; height: 300px; background: #f5f7fa; color: #909399; border-radius: 8px;">暂无图片</div>
        </div>
        <el-descriptions :column="2" border style="margin-top: 20px;">
          <el-descriptions-item label="公寓名称">{{ currentApartment?.name }}</el-descriptions-item>
          <el-descriptions-item label="地址">{{ currentApartment?.address }}</el-descriptions-item>
          <el-descriptions-item label="楼层">{{ currentApartment?.floor || '-' }}层</el-descriptions-item>
          <el-descriptions-item label="面积">{{ currentApartment?.area || '-' }} ㎡</el-descriptions-item>
          <el-descriptions-item label="月租">¥{{ formatMoney(currentApartment?.monthlyRent) }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentApartment?.status === '空置' ? 'success' : 'info'">{{ currentApartment?.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="房东">{{ currentApartment?.landlord?.realName || '-' }} (ID:{{ currentApartment?.landlord?.id }})</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ currentApartment?.landlord?.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ currentApartment?.description || '暂无描述' }}</el-descriptions-item>
          <el-descriptions-item label="审核状态">
            <el-tag :type="getAuditStatusType(currentApartment?.auditStatus)">{{ currentApartment?.auditStatus }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="审核备注">{{ currentApartment?.auditRemark || '-' }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="viewDialogVisible = false">关闭</el-button>
        <template v-if="currentApartment?.auditStatus === '待审核'">
          <el-button type="success" @click="handleAudit(currentApartment, '审核通过')">通过</el-button>
          <el-button type="danger" @click="showRejectDialog(currentApartment)">拒绝</el-button>
        </template>
      </template>
    </el-dialog>

    <el-dialog v-model="rejectDialogVisible" title="审核拒绝" width="400px">
      <el-form :model="rejectForm" label-width="80px">
        <el-form-item label="拒绝原因">
          <el-input v-model="rejectForm.remark" type="textarea" :rows="3" placeholder="请输入拒绝原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmReject">确认拒绝</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { getApartments, getPendingAuditApartments, auditApartment, deleteApartment } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'AdminApartments',
  data() {
    return {
      apartments: [],
      loading: false,
      activeTab: 'pending',
      viewDialogVisible: false,
      rejectDialogVisible: false,
      currentApartment: null,
      rejectForm: { remark: '' }
    }
  },
  computed: {
    pendingApartments() { return this.apartments.filter(a => a.auditStatus === '待审核') },
    auditedApartments() { return this.apartments.filter(a => a.auditStatus !== '待审核') },
    detailImages() { return this.currentApartment?.detailImages ? this.currentApartment.detailImages.split(',').filter(img => img) : [] }
  },
  created() { this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try { this.apartments = (await getApartments()).data } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    viewApartment(row) { this.currentApartment = row; this.viewDialogVisible = true },
    async handleAudit(row, status) {
      ElMessageBox.confirm(`确定要${status}该房源吗？`, '提示', { type: 'warning' }).then(async () => {
        await auditApartment(row.id, status, '')
        ElMessage.success(`${status}成功`)
        this.viewDialogVisible = false
        this.loadData()
      }).catch(() => {})
    },
    showRejectDialog(row) { this.currentApartment = row; this.rejectForm.remark = ''; this.rejectDialogVisible = true },
    async confirmReject() {
      await auditApartment(this.currentApartment.id, '审核拒绝', this.rejectForm.remark)
      ElMessage.success('已拒绝')
      this.rejectDialogVisible = false
      this.viewDialogVisible = false
      this.loadData()
    },
    handleDelete(row) {
      ElMessageBox.confirm('确定要删除该公寓吗？', '提示', { type: 'warning' }).then(async () => {
        await deleteApartment(row.id)
        ElMessage.success('删除成功')
        this.loadData()
      }).catch(() => {})
    },
    formatMoney(v) { return v ? parseFloat(v).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) : '-' },
    getAuditStatusType(s) { return { '待审核': 'warning', '审核通过': 'success', '审核拒绝': 'danger' }[s] || 'info' },
    formatTime(time) {
      if (!time) return '-'
      const date = new Date(time)
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
    }
  }
}
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.detail-content { padding: 10px 0; }
.no-detail-images { width: 100%; }
</style>
