<template>
  <div class="apartments">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>我的公寓</span>
          <el-button type="primary" @click="handleAdd">发布公寓</el-button>
        </div>
      </template>
      <el-table :data="apartments" v-loading="loading" stripe>
        <el-table-column label="封面" width="90">
          <template #default="scope">
            <el-image v-if="scope.row.coverImage" :src="getImageUrl(scope.row.coverImage)" style="width: 60px; height: 60px; border-radius: 6px;" fit="cover" :preview-src-list="[getImageUrl(scope.row.coverImage)]" />
            <span v-else style="color: #909399;">暂无</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="公寓名称" min-width="140" />
        <el-table-column prop="address" label="地址" min-width="180" show-overflow-tooltip />
        <el-table-column prop="area" label="面积(㎡)" min-width="90">
          <template #default="scope">{{ scope.row.area || '-' }}</template>
        </el-table-column>
        <el-table-column prop="monthlyRent" label="月租(元)" min-width="100">
          <template #default="scope">{{ formatMoney(scope.row.monthlyRent) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" min-width="80">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="auditStatus" label="审核状态" min-width="90">
          <template #default="scope">
            <el-tag :type="getAuditStatusType(scope.row.auditStatus)">{{ scope.row.auditStatus }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="scope">
            <el-button size="small" link @click="handleEdit(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" link @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px">
      <el-form :model="form" :rules="rules" ref="aptForm" label-width="100px">
        <el-form-item label="公寓名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入公寓名称" />
        </el-form-item>
        <el-form-item label="地址" prop="address">
          <el-input v-model="form.address" placeholder="请输入地址" />
        </el-form-item>
        <el-row>
          <el-col :span="12">
            <el-form-item label="楼层">
              <el-input v-model="form.floor" placeholder="楼层" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="面积(㎡)">
              <el-input-number v-model="form.area" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="12">
            <el-form-item label="月租(元)" prop="monthlyRent">
              <el-input-number v-model="form.monthlyRent" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width: 100%">
                <el-option label="空置" value="空置" />
                <el-option label="已出租" value="已出租" />
                <el-option label="维修中" value="维修中" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        
        <el-form-item label="封面图片">
          <div class="upload-container">
            <el-upload
              class="cover-uploader"
              :action="uploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleCoverSuccess"
              :before-upload="beforeUpload"
              accept="image/*"
            >
              <el-image v-if="form.coverImage" :src="getImageUrl(form.coverImage)" class="cover-image" fit="cover" />
              <div v-else class="upload-placeholder">
                <el-icon class="upload-icon"><Plus /></el-icon>
                <span>上传封面</span>
              </div>
            </el-upload>
            <div class="upload-tip">点击上传封面图片，支持 jpg/png 格式，大小不超过 5MB</div>
          </div>
        </el-form-item>
        
        <el-form-item label="详细图片">
          <div class="detail-images-container">
            <div v-for="(img, index) in detailImageList" :key="index" class="detail-image-item">
              <el-image :src="getImageUrl(img)" class="detail-image" fit="cover" :preview-src-list="detailImageList.map(i => getImageUrl(i))" />
              <div class="image-actions">
                <el-button type="danger" size="small" circle @click="removeDetailImage(index)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            <el-upload
              class="detail-uploader"
              :action="uploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleDetailSuccess"
              :before-upload="beforeUpload"
              accept="image/*"
            >
              <div class="upload-placeholder-small">
                <el-icon class="upload-icon-small"><Plus /></el-icon>
                <span>添加图片</span>
              </div>
            </el-upload>
          </div>
          <div class="upload-tip">可上传多张详细图片，支持 jpg/png 格式</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">提交审核</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { getApartmentsByLandlord, createApartment, updateApartment, deleteApartment } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'

export default {
  name: 'LandlordApartments',
  components: { Plus, Delete },
  data() {
    return {
      apartments: [],
      loading: false,
      dialogVisible: false,
      dialogTitle: '发布公寓',
      editId: null,
      form: { name: '', address: '', floor: '', area: null, monthlyRent: null, status: '空置', description: '', coverImage: '', detailImages: '' },
      detailImageList: [],
      rules: {
        name: [{ required: true, message: '请输入公寓名称', trigger: 'blur' }],
        monthlyRent: [{ required: true, message: '请输入月租', trigger: 'blur' }]
      },
      uploadUrl: '/api/upload',
      uploadHeaders: { Authorization: localStorage.getItem('token') ? 'Bearer ' + localStorage.getItem('token') : '' }
    }
  },
  created() { this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const userId = localStorage.getItem('userId')
        this.apartments = (await getApartmentsByLandlord(userId)).data
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    handleAdd() {
      this.editId = null
      this.dialogTitle = '发布公寓'
      this.form = { name: '', address: '', floor: '', area: null, monthlyRent: null, status: '空置', description: '', coverImage: '', detailImages: '' }
      this.detailImageList = []
      this.dialogVisible = true
    },
    handleEdit(row) {
      this.editId = row.id
      this.dialogTitle = '编辑公寓'
      this.form = { ...row }
      this.detailImageList = row.detailImages ? row.detailImages.split(',').filter(img => img) : []
      this.dialogVisible = true
    },
    handleDelete(row) {
      ElMessageBox.confirm('确定要删除该公寓吗？', '提示', { type: 'warning' }).then(async () => {
        await deleteApartment(row.id)
        ElMessage.success('删除成功')
        this.loadData()
      }).catch(() => {})
    },
    beforeUpload(file) {
      const isImage = file.type.startsWith('image/')
      const isLt5M = file.size / 1024 / 1024 < 5
      if (!isImage) {
        ElMessage.error('只能上传图片文件!')
        return false
      }
      if (!isLt5M) {
        ElMessage.error('图片大小不能超过 5MB!')
        return false
      }
      return true
    },
    handleCoverSuccess(response) {
      if (response.code === 200) {
        this.form.coverImage = response.data
        ElMessage.success('封面上传成功')
      } else {
        ElMessage.error(response.message || '上传失败')
      }
    },
    handleDetailSuccess(response) {
      if (response.code === 200) {
        this.detailImageList.push(response.data)
        ElMessage.success('图片上传成功')
      } else {
        ElMessage.error(response.message || '上传失败')
      }
    },
    removeDetailImage(index) {
      this.detailImageList.splice(index, 1)
    },
    getImageUrl(path) {
      if (!path) return ''
      if (path.startsWith('http')) return path
      return 'http://localhost:8080' + path
    },
    handleSubmit() {
      this.$refs.aptForm.validate(async (valid) => {
        if (valid) {
          try {
            const userId = localStorage.getItem('userId')
            const data = {
              ...this.form,
              detailImages: this.detailImageList.join(','),
              landlord: { id: userId },
              auditStatus: '待审核'
            }
            if (this.editId) {
              await updateApartment(this.editId, data)
              ElMessage.success('更新成功，已重新提交审核')
            } else {
              await createApartment(data)
              ElMessage.success('发布成功，等待审核')
            }
            this.dialogVisible = false
            this.loadData()
          } catch (e) { console.error(e) }
        }
      })
    },
    formatMoney(v) { return v ? parseFloat(v).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) : '-' },
    getStatusType(s) { return { '空置': '', '已出租': 'success', '维修中': 'warning' }[s] || '' },
    getAuditStatusType(s) { return { '待审核': 'warning', '审核通过': 'success', '审核拒绝': 'danger' }[s] || 'info' }
  }
}
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }

.upload-container { display: flex; flex-direction: column; align-items: flex-start; }

.cover-uploader {
  border: 1px dashed #d9d9d9;
  border-radius: 8px;
  cursor: pointer;
  overflow: hidden;
  width: 200px;
  height: 150px;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: border-color 0.3s;
}

.cover-uploader:hover {
  border-color: #409eff;
}

.cover-image {
  width: 200px;
  height: 150px;
  display: block;
  object-fit: cover;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #8c939d;
}

.upload-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.upload-placeholder span {
  font-size: 14px;
}

.upload-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 8px;
}

.detail-images-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.detail-image-item {
  position: relative;
  width: 120px;
  height: 90px;
}

.detail-image {
  width: 120px;
  height: 90px;
  border-radius: 6px;
  object-fit: cover;
}

.image-actions {
  position: absolute;
  top: -8px;
  right: -8px;
}

.detail-uploader {
  width: 120px;
  height: 90px;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: border-color 0.3s;
}

.detail-uploader:hover {
  border-color: #409eff;
}

.upload-placeholder-small {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #8c939d;
}

.upload-icon-small {
  font-size: 24px;
  margin-bottom: 4px;
}

.upload-placeholder-small span {
  font-size: 12px;
}
</style>
