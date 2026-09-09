<template>
  <div class="payments">
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>支付管理</span>
          <el-button type="primary" @click="showCreateDialog">发送支付请求</el-button>
        </div>
      </template>
      <el-table :data="payments" v-loading="loading" stripe>
        <el-table-column prop="paymentNo" label="缴费编号" min-width="150" />
        <el-table-column label="合同" min-width="140">
          <template #default="scope">
            <div>{{ scope.row.contract?.contractNo || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="租户" min-width="140">
          <template #default="scope">
            <div>ID:{{ scope.row.tenant?.id }}</div>
            <div style="color: #909399; font-size: 12px;">{{ scope.row.tenant?.realName || scope.row.tenant?.username || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="paymentDate" label="缴费日期" min-width="110" />
        <el-table-column prop="amount" label="金额(元)" min-width="100">
          <template #default="scope">{{ formatMoney(scope.row.amount) }}</template>
        </el-table-column>
        <el-table-column prop="paymentType" label="类型" min-width="80">
          <template #default="scope">
            <el-tag :type="getPaymentTypeTag(scope.row.paymentType)">{{ scope.row.paymentType }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" min-width="90">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="scope">
            <el-button size="small" link @click="viewPayment(scope.row)">查看</el-button>
            <el-button size="small" type="danger" link @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="createDialogVisible" title="发送支付请求" width="550px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="选择合同" prop="contractId">
          <el-select v-model="form.contractId" placeholder="请选择已生效合同" style="width: 100%" @change="onContractChange">
            <el-option v-for="c in activeContracts" :key="c.id" :label="`合同ID:${c.id} - 租户ID:${c.tenant?.id} (${c.tenant?.realName || c.tenant?.username || '-'})`" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="租户">
          <el-input :value="selectedTenantInfo" disabled />
        </el-form-item>
        <el-form-item label="缴费日期" prop="paymentDate">
          <el-date-picker v-model="form.paymentDate" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="金额(元)" prop="amount">
          <el-input-number v-model="form.amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="类型" prop="paymentType">
          <el-select v-model="form.paymentType" placeholder="请选择" style="width: 100%" @change="onPaymentTypeChange">
            <el-option label="租金" value="租金" />
            <el-option label="押金" value="押金" />
            <el-option label="水电费" value="水电费" />
            <el-option label="维修费" value="维修费" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="凭证图片" prop="voucherFile" v-if="showVoucherUpload">
          <el-upload
            class="voucher-uploader"
            :action="uploadUrl"
            :headers="uploadHeaders"
            :show-file-list="false"
            :on-success="handleUploadSuccess"
            :before-upload="beforeUpload"
            accept="image/*"
          >
            <img v-if="form.paymentVoucher" :src="getVoucherUrl(form.paymentVoucher)" class="voucher-image" />
            <el-icon v-else class="voucher-uploader-icon"><Plus /></el-icon>
          </el-upload>
          <div class="upload-tip">维修费、水电费需要上传凭证图片</div>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">发送</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="viewDialogVisible" title="支付详情" width="550px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="缴费编号">{{ currentPayment.paymentNo }}</el-descriptions-item>
        <el-descriptions-item label="合同编号">{{ currentPayment.contract?.contractNo }}</el-descriptions-item>
        <el-descriptions-item label="租户">ID:{{ currentPayment.tenant?.id }} ({{ currentPayment.tenant?.realName || currentPayment.tenant?.username || '-' }})</el-descriptions-item>
        <el-descriptions-item label="缴费日期">{{ currentPayment.paymentDate }}</el-descriptions-item>
        <el-descriptions-item label="金额">{{ formatMoney(currentPayment.amount) }} 元</el-descriptions-item>
        <el-descriptions-item label="类型">
          <el-tag :type="getPaymentTypeTag(currentPayment.paymentType)">{{ currentPayment.paymentType }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="支付方式">{{ currentPayment.paymentMethod || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentPayment.status)">{{ currentPayment.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="支付时间">{{ currentPayment.payTime || '-' }}</el-descriptions-item>
        <el-descriptions-item label="支付凭证" v-if="currentPayment.paymentVoucher">
          <el-image 
            :src="getVoucherUrl(currentPayment.paymentVoucher)" 
            :preview-src-list="[getVoucherUrl(currentPayment.paymentVoucher)]"
            style="width: 100px; height: 100px;"
            fit="cover"
          />
        </el-descriptions-item>
        <el-descriptions-item label="备注">{{ currentPayment.remark || '-' }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="viewDialogVisible = false">关闭</el-button>
        <el-button type="danger" @click="handleDelete(currentPayment)">删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { getPaymentsByLandlord, getContractsByLandlord, createPayment, deletePayment } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

export default {
  name: 'LandlordPayments',
  components: { Plus },
  data() {
    const validateVoucher = (rule, value, callback) => {
      if (this.showVoucherUpload && !this.form.paymentVoucher) {
        callback(new Error('请上传凭证图片'))
      } else {
        callback()
      }
    }
    return {
      payments: [],
      activeContracts: [],
      loading: false,
      createDialogVisible: false,
      viewDialogVisible: false,
      currentPayment: {},
      form: { contractId: null, paymentDate: '', amount: 0, paymentType: '租金', remark: '', paymentVoucher: '' },
      rules: {
        contractId: [{ required: true, message: '请选择合同', trigger: 'change' }],
        paymentDate: [{ required: true, message: '请选择日期', trigger: 'change' }],
        amount: [{ required: true, message: '请输入金额', trigger: 'blur' }],
        paymentType: [{ required: true, message: '请选择类型', trigger: 'change' }],
        voucherFile: [{ validator: validateVoucher, trigger: 'change' }]
      },
      uploadUrl: '/api/upload',
      uploadHeaders: { Authorization: localStorage.getItem('token') ? 'Bearer ' + localStorage.getItem('token') : '' }
    }
  },
  computed: {
    selectedTenantInfo() {
      const c = this.activeContracts.find(x => x.id === this.form.contractId)
      if (!c) return ''
      return `ID:${c.tenant?.id} (${c.tenant?.realName || c.tenant?.username || '-'})`
    },
    showVoucherUpload() {
      return ['水电费', '维修费'].includes(this.form.paymentType)
    }
  },
  created() { this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const userId = localStorage.getItem('userId')
        const [payRes, conRes] = await Promise.all([
          getPaymentsByLandlord(userId),
          getContractsByLandlord(userId)
        ])
        this.payments = payRes.data
        this.activeContracts = conRes.data.filter(c => c.status === '生效中')
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    showCreateDialog() {
      this.form = { contractId: null, paymentDate: '', amount: 0, paymentType: '租金', remark: '', paymentVoucher: '' }
      this.createDialogVisible = true
    },
    onContractChange(contractId) {
      const c = this.activeContracts.find(x => x.id === contractId)
      if (c) this.form.amount = c.monthlyRent
    },
    onPaymentTypeChange() {
      if (!this.showVoucherUpload) {
        this.form.paymentVoucher = ''
      }
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
    handleUploadSuccess(response) {
      if (response.code === 200) {
        this.form.paymentVoucher = response.data
        ElMessage.success('上传成功')
      } else {
        ElMessage.error(response.message || '上传失败')
      }
    },
    getVoucherUrl(path) {
      if (!path) return ''
      if (path.startsWith('http')) return path
      return 'http://localhost:8080' + path
    },
    handleCreate() {
      this.$refs.formRef.validate(async (valid) => {
        if (valid) {
          const contract = this.activeContracts.find(c => c.id === this.form.contractId)
          const userId = localStorage.getItem('userId')
          await createPayment({
            contract: { id: this.form.contractId },
            tenant: { id: contract.tenant.id },
            landlord: { id: userId },
            paymentDate: this.form.paymentDate,
            amount: this.form.amount,
            paymentType: this.form.paymentType,
            status: '待支付',
            remark: this.form.remark,
            paymentVoucher: this.form.paymentVoucher
          })
          ElMessage.success('支付请求已发送')
          this.createDialogVisible = false
          this.loadData()
        }
      })
    },
    viewPayment(row) {
      this.currentPayment = row
      this.viewDialogVisible = true
    },
    handleDelete(row) {
      ElMessageBox.confirm('确定要删除该支付记录吗？', '提示', { type: 'warning' }).then(async () => {
        await deletePayment(row.id)
        ElMessage.success('删除成功')
        this.viewDialogVisible = false
        this.loadData()
      }).catch(() => {})
    },
    formatMoney(v) { return v ? parseFloat(v).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) : '-' },
    getStatusType(s) {
      const map = { '待支付': 'warning', '已支付': 'success' }
      return map[s] || 'info'
    },
    getPaymentTypeTag(t) {
      const map = { '租金': 'primary', '押金': 'success', '水电费': 'warning', '维修费': 'danger', '其他': 'info' }
      return map[t] || 'info'
    }
  }
}
</script>

<style scoped>
.voucher-uploader {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  width: 148px;
  height: 148px;
  display: flex;
  justify-content: center;
  align-items: center;
}
.voucher-uploader:hover {
  border-color: #409eff;
}
.voucher-uploader-icon {
  font-size: 28px;
  color: #8c939d;
}
.voucher-image {
  width: 148px;
  height: 148px;
  display: block;
  object-fit: cover;
}
.upload-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 8px;
}
</style>
