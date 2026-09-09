<template>
  <div class="payments">
    <el-card>
      <template #header><span>缴费记录</span></template>
      <el-table :data="payments" v-loading="loading" stripe>
        <el-table-column prop="paymentNo" label="缴费编号" min-width="150" />
        <el-table-column label="合同" min-width="140">
          <template #default="scope">{{ scope.row.contract?.contractNo || '-' }}</template>
        </el-table-column>
        <el-table-column label="房东" min-width="140">
          <template #default="scope">
            <div>ID:{{ scope.row.landlord?.id }}</div>
            <div style="color: #909399; font-size: 12px;">{{ scope.row.landlord?.realName || scope.row.landlord?.username || '-' }}</div>
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
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="scope">
            <el-button size="small" link @click="viewPayment(scope.row)">查看</el-button>
            <el-button size="small" type="success" link @click="openPayDialog(scope.row)" v-if="scope.row.status === '待支付'">支付</el-button>
            <el-button size="small" type="danger" link @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="payDialogVisible" title="支付" width="450px">
      <el-descriptions :column="1" border size="small">
        <el-descriptions-item label="缴费编号">{{ currentPayment.paymentNo }}</el-descriptions-item>
        <el-descriptions-item label="金额">
          <span style="font-size: 20px; color: #f56c6c; font-weight: bold;">{{ formatMoney(currentPayment.amount) }} 元</span>
        </el-descriptions-item>
        <el-descriptions-item label="类型">{{ currentPayment.paymentType }}</el-descriptions-item>
        <el-descriptions-item label="凭证" v-if="currentPayment.paymentVoucher && ['水电费', '维修费'].includes(currentPayment.paymentType)">
          <el-image 
            :src="getVoucherUrl(currentPayment.paymentVoucher)" 
            :preview-src-list="[getVoucherUrl(currentPayment.paymentVoucher)]"
            style="width: 80px; height: 80px;"
            fit="cover"
          />
        </el-descriptions-item>
      </el-descriptions>
      <el-divider />
      <el-form :model="payForm" :rules="payRules" ref="payFormRef" label-width="80px">
        <el-form-item label="支付方式" prop="paymentMethod">
          <el-radio-group v-model="payForm.paymentMethod">
            <el-radio label="微信支付">
              <span style="display: inline-flex; align-items: center;">
                <span style="color: #07c160; font-size: 18px; margin-right: 4px;">&#x1F4AC;</span> 微信支付
              </span>
            </el-radio>
            <el-radio label="支付宝">
              <span style="display: inline-flex; align-items: center;">
                <span style="color: #1677ff; font-size: 18px; margin-right: 4px;">&#x1F4B3;</span> 支付宝
              </span>
            </el-radio>
            <el-radio label="银行卡">
              <span style="display: inline-flex; align-items: center;">
                <span style="color: #faad14; font-size: 18px; margin-right: 4px;">&#x1F4F1;</span> 银行卡
              </span>
            </el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="支付凭证">
          <el-input v-model="payForm.paymentVoucher" placeholder="请输入支付凭证（模拟）" />
          <div style="color: #909399; font-size: 12px; margin-top: 4px;">示例：WX20240101123456、ALI20240101123456、BANK20240101123456</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="payDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handlePay" :loading="paying">确认支付</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="viewDialogVisible" title="支付详情" width="550px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="缴费编号">{{ currentPayment.paymentNo }}</el-descriptions-item>
        <el-descriptions-item label="合同编号">{{ currentPayment.contract?.contractNo }}</el-descriptions-item>
        <el-descriptions-item label="房东">ID:{{ currentPayment.landlord?.id }} ({{ currentPayment.landlord?.realName || currentPayment.landlord?.username || '-' }})</el-descriptions-item>
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
        <el-descriptions-item label="凭证图片" v-if="currentPayment.paymentVoucher && ['水电费', '维修费'].includes(currentPayment.paymentType)">
          <el-image 
            :src="getVoucherUrl(currentPayment.paymentVoucher)" 
            :preview-src-list="[getVoucherUrl(currentPayment.paymentVoucher)]"
            style="width: 100px; height: 100px;"
            fit="cover"
          />
        </el-descriptions-item>
        <el-descriptions-item label="支付凭证" v-else-if="currentPayment.paymentVoucher">
          <el-tag type="success">{{ currentPayment.paymentVoucher }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="备注">{{ currentPayment.remark || '-' }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="viewDialogVisible = false">关闭</el-button>
        <el-button type="danger" @click="handleDelete(currentPayment)">删除</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="successDialogVisible" title="支付成功" width="400px" center>
      <div style="text-align: center; padding: 20px;">
        <el-icon style="font-size: 60px; color: #67c23a;"><SuccessFilled /></el-icon>
        <h3 style="margin: 15px 0;">支付成功！</h3>
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="缴费编号">{{ paidPayment.paymentNo }}</el-descriptions-item>
          <el-descriptions-item label="支付金额">{{ formatMoney(paidPayment.amount) }} 元</el-descriptions-item>
          <el-descriptions-item label="支付方式">{{ paidPayment.paymentMethod }}</el-descriptions-item>
          <el-descriptions-item label="支付凭证">
            <el-tag type="success">{{ paidPayment.paymentVoucher }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="支付时间">{{ paidPayment.payTime }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button type="primary" @click="successDialogVisible = false">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { getPaymentsByTenant, updatePayment, deletePayment } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { SuccessFilled } from '@element-plus/icons-vue'

export default {
  name: 'TenantPayments',
  components: { SuccessFilled },
  data() {
    return {
      payments: [],
      loading: false,
      payDialogVisible: false,
      viewDialogVisible: false,
      successDialogVisible: false,
      paying: false,
      currentPayment: {},
      paidPayment: {},
      payForm: { paymentMethod: '微信支付', paymentVoucher: '' },
      payRules: {
        paymentMethod: [{ required: true, message: '请选择支付方式', trigger: 'change' }]
      }
    }
  },
  created() { this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const userId = localStorage.getItem('userId')
        this.payments = (await getPaymentsByTenant(userId)).data
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    openPayDialog(row) {
      this.currentPayment = row
      this.payForm = { paymentMethod: '微信支付', paymentVoucher: this.generateVoucher('WX') }
      this.payDialogVisible = true
    },
    generateVoucher(prefix) {
      const now = new Date()
      const dateStr = now.getFullYear().toString() +
        (now.getMonth() + 1).toString().padStart(2, '0') +
        now.getDate().toString().padStart(2, '0') +
        now.getHours().toString().padStart(2, '0') +
        now.getMinutes().toString().padStart(2, '0') +
        now.getSeconds().toString().padStart(2, '0')
      return prefix + dateStr + Math.floor(Math.random() * 1000).toString().padStart(3, '0')
    },
    handlePay() {
      this.$refs.payFormRef.validate(async (valid) => {
        if (valid) {
          this.paying = true
          try {
            const prefix = this.payForm.paymentMethod === '微信支付' ? 'WX' : 
                          this.payForm.paymentMethod === '支付宝' ? 'ALI' : 'BANK'
            const voucher = this.payForm.paymentVoucher || this.generateVoucher(prefix)
            const now = new Date()
            const payTime = now.getFullYear() + '-' + 
              (now.getMonth() + 1).toString().padStart(2, '0') + '-' +
              now.getDate().toString().padStart(2, '0') + ' ' +
              now.getHours().toString().padStart(2, '0') + ':' +
              now.getMinutes().toString().padStart(2, '0') + ':' +
              now.getSeconds().toString().padStart(2, '0')
            await updatePayment(this.currentPayment.id, {
              ...this.currentPayment,
              status: '已支付',
              paymentMethod: this.payForm.paymentMethod,
              paymentVoucher: voucher,
              payTime: payTime
            })
            this.paidPayment = {
              ...this.currentPayment,
              status: '已支付',
              paymentMethod: this.payForm.paymentMethod,
              paymentVoucher: voucher,
              payTime: payTime
            }
            this.payDialogVisible = false
            this.successDialogVisible = true
            this.loadData()
          } catch (e) { 
            console.error(e)
            ElMessage.error('支付失败')
          }
          finally { this.paying = false }
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
    },
    getVoucherUrl(path) {
      if (!path) return ''
      if (path.startsWith('http')) return path
      if (path.startsWith('/uploads')) return 'http://localhost:8080' + path
      return path
    }
  }
}
</script>
