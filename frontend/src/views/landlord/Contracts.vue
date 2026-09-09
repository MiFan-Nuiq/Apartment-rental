<template>
  <div class="contracts">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>合同管理</span>
          <el-button type="primary" @click="handleAdd">创建合同</el-button>
        </div>
      </template>
      <el-table :data="contracts" v-loading="loading" stripe>
        <el-table-column prop="contractNo" label="合同编号" min-width="150" />
        <el-table-column label="公寓" min-width="120">
          <template #default="scope">
            <div>ID:{{ scope.row.apartment?.id }}</div>
            <div style="color: #909399; font-size: 12px;">{{ scope.row.apartment?.name || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="租户" min-width="120">
          <template #default="scope">
            <div>ID:{{ scope.row.tenant?.id }}</div>
            <div style="color: #909399; font-size: 12px;">{{ scope.row.tenant?.realName || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="startDate" label="开始日期" min-width="110" />
        <el-table-column prop="endDate" label="结束日期" min-width="110" />
        <el-table-column prop="monthlyRent" label="月租(元)" min-width="100">
          <template #default="scope">{{ formatMoney(scope.row.monthlyRent) }}</template>
        </el-table-column>
        <el-table-column prop="contractType" label="类型" min-width="80">
          <template #default="scope">
            <el-tag :type="scope.row.contractType === '续租' ? 'warning' : 'primary'" size="small">{{ scope.row.contractType }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" min-width="90">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="scope">
            <el-button size="small" link @click="handleView(scope.row)">查看</el-button>
            <el-button size="small" type="danger" link @click="handleTerminate(scope.row)" v-if="scope.row.status === '生效中' && scope.row.subletStatus !== '待确认'">解约</el-button>
            <el-button size="small" type="success" link @click="handleConfirmSublet(scope.row)" v-if="scope.row.subletStatus === '待确认'">确认转租</el-button>
            <el-button size="small" type="warning" link @click="handleRejectSublet(scope.row)" v-if="scope.row.subletStatus === '待确认'">拒绝转租</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="创建合同" width="600px">
      <el-form :model="form" :rules="rules" ref="contractForm" label-width="100px">
        <el-form-item label="选择预约" prop="appointmentId">
          <el-select v-model="form.appointmentId" placeholder="请选择已接受的预约" style="width: 100%" @change="handleAppointmentChange">
            <el-option v-for="item in acceptedAppointments" :key="item.id" :label="`预约ID:${item.id} - 租户ID:${item.tenant?.id} (${item.tenant?.realName || item.tenant?.username || '-'})`" :value="item.id">
              <span>预约ID:{{ item.id }} - 租户ID:{{ item.tenant?.id }} ({{ item.tenant?.realName || item.tenant?.username || '-' }})</span>
              <el-tag type="info" size="small" style="margin-left: 10px;">公寓ID:{{ item.apartment?.id }}</el-tag>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="公寓ID">
          <el-input :value="selectedApartment?.id || '-'" disabled />
        </el-form-item>
        <el-form-item label="租户ID">
          <el-input :value="selectedTenant?.id || '-'" disabled />
        </el-form-item>
        <el-row>
          <el-col :span="12">
            <el-form-item label="开始日期" prop="startDate">
              <el-date-picker v-model="form.startDate" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束日期" prop="endDate">
              <el-date-picker v-model="form.endDate" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
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
            <el-form-item label="押金(元)">
              <el-input-number v-model="form.deposit" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="付款方式">
          <el-select v-model="form.paymentMethod" style="width: 100%">
            <el-option label="月付" value="月付" />
            <el-option label="季付" value="季付" />
            <el-option label="半年付" value="半年付" />
            <el-option label="年付" value="年付" />
          </el-select>
        </el-form-item>
        <el-alert type="info" :closable="false" style="margin-top: 10px;">
          <template #title>提示：只能向已接受预约的租户发起合同。创建后需要租户确认，确认后房源状态才会变为"已出租"。</template>
        </el-alert>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">创建并发送给租户确认</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="viewDialogVisible" title="合同详情" width="700px">
      <div class="contract-template" v-if="currentContract">
        <h2 style="text-align: center; margin-bottom: 20px;">房屋租赁合同</h2>
        <el-divider />
        <p><strong>合同编号：</strong>{{ currentContract.contractNo }}</p>
        <p><strong>合同类型：</strong>
          <el-tag :type="currentContract.contractType === '续租' ? 'warning' : 'primary'" size="small">{{ currentContract.contractType }}</el-tag>
        </p>
        <p v-if="currentContract.originalContractId"><strong>原合同ID：</strong>{{ currentContract.originalContractId }}</p>
        <p><strong>出租方ID：</strong>{{ currentContract.landlord?.id }}</p>
        <p><strong>承租方ID：</strong>{{ currentContract.tenant?.id }}</p>
        <p><strong>公寓ID：</strong>{{ currentContract.apartment?.id }}</p>
        <p><strong>房屋地址：</strong>{{ currentContract.apartment?.address || '-' }} {{ currentContract.apartment?.name }}</p>
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
        <p><strong>转租状态：</strong><el-tag :type="getSubletStatusType(currentContract.subletStatus)" size="small">{{ currentContract.subletStatus }}</el-tag></p>
        <p v-if="currentContract.subletStatus === '待确认'"><strong>新租户ID：</strong>{{ currentContract.newTenant?.id }}</p>
        <p><strong>合同状态：</strong><el-tag :type="getStatusType(currentContract.status)">{{ currentContract.status }}</el-tag></p>
        <p v-if="currentContract.terminateReason"><strong>解约原因：</strong>{{ currentContract.terminateReason }}</p>
        <p v-if="currentContract.terminateTime"><strong>解约时间：</strong>{{ currentContract.terminateTime }}</p>
        <p><strong>签订日期：</strong>{{ currentContract.createTime }}</p>
      </div>
      <template #footer>
        <el-button @click="viewDialogVisible = false">关闭</el-button>
        <el-button type="danger" @click="handleTerminate(currentContract)" v-if="currentContract?.status === '生效中' && currentContract?.subletStatus !== '待确认'">解约</el-button>
        <el-button type="success" @click="handleConfirmSublet(currentContract)" v-if="currentContract?.subletStatus === '待确认'">确认转租</el-button>
        <el-button type="warning" @click="handleRejectSublet(currentContract)" v-if="currentContract?.subletStatus === '待确认'">拒绝转租</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="terminateDialogVisible" title="解约确认" width="400px">
      <el-form :model="terminateForm" label-width="80px">
        <el-form-item label="解约原因">
          <el-input v-model="terminateForm.reason" type="textarea" :rows="3" placeholder="请输入解约原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="terminateDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmTerminate">确认解约</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { getContractsByLandlord, createContract, getAcceptedTenantsByLandlord, terminateContract, confirmSublet, rejectSublet } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'LandlordContracts',
  data() {
    return {
      contracts: [],
      acceptedAppointments: [],
      loading: false,
      dialogVisible: false,
      viewDialogVisible: false,
      terminateDialogVisible: false,
      currentContract: null,
      form: { appointmentId: null, startDate: '', endDate: '', monthlyRent: null, deposit: null, paymentMethod: '月付' },
      terminateForm: { reason: '' },
      rules: {
        appointmentId: [{ required: true, message: '请选择预约', trigger: 'change' }],
        startDate: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
        endDate: [{ required: true, message: '请选择结束日期', trigger: 'change' }],
        monthlyRent: [{ required: true, message: '请输入月租', trigger: 'blur' }]
      }
    }
  },
  computed: {
    selectedAppointment() {
      return this.acceptedAppointments.find(a => a.id === this.form.appointmentId)
    },
    selectedApartment() {
      return this.selectedAppointment?.apartment
    },
    selectedTenant() {
      return this.selectedAppointment?.tenant
    }
  },
  created() { this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const userId = localStorage.getItem('userId')
        const [contracts, appointments] = await Promise.all([
          getContractsByLandlord(userId),
          getAcceptedTenantsByLandlord(userId)
        ])
        this.contracts = contracts.data
        this.acceptedAppointments = appointments.data
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    handleAdd() {
      this.form = { appointmentId: null, startDate: '', endDate: '', monthlyRent: null, deposit: null, paymentMethod: '月付' }
      this.dialogVisible = true
    },
    handleView(contract) {
      this.currentContract = contract
      this.viewDialogVisible = true
    },
    handleTerminate(contract) {
      this.currentContract = contract
      this.terminateForm.reason = ''
      this.terminateDialogVisible = true
    },
    async confirmTerminate() {
      try {
        await terminateContract(this.currentContract.id, this.terminateForm.reason)
        ElMessage.success('解约成功')
        this.terminateDialogVisible = false
        this.viewDialogVisible = false
        this.loadData()
      } catch (e) {
        ElMessage.error(e.response?.data?.message || '解约失败')
      }
    },
    async handleConfirmSublet(contract) {
      ElMessageBox.confirm(`确认将合同转租给租户ID:${contract.newTenant?.id}吗？`, '确认转租', { type: 'warning' }).then(async () => {
        await confirmSublet(contract.id)
        ElMessage.success('转租成功')
        this.viewDialogVisible = false
        this.loadData()
      }).catch(() => {})
    },
    async handleRejectSublet(contract) {
      ElMessageBox.confirm('确定要拒绝此转租申请吗？', '拒绝转租', { type: 'warning' }).then(async () => {
        await rejectSublet(contract.id)
        ElMessage.success('已拒绝转租')
        this.viewDialogVisible = false
        this.loadData()
      }).catch(() => {})
    },
    handleAppointmentChange(appointmentId) {
      const apt = this.selectedApartment
      if (apt) this.form.monthlyRent = apt.monthlyRent
    },
    handleSubmit() {
      this.$refs.contractForm.validate(async (valid) => {
        if (valid) {
          try {
            const userId = localStorage.getItem('userId')
            const appointment = this.selectedAppointment
            const data = {
              apartment: { id: appointment.apartment.id },
              tenant: { id: appointment.tenant.id },
              landlord: { id: userId },
              startDate: this.form.startDate,
              endDate: this.form.endDate,
              monthlyRent: this.form.monthlyRent,
              deposit: this.form.deposit,
              paymentMethod: this.form.paymentMethod,
              status: '待确认',
              contractType: '新签'
            }
            await createContract(data)
            ElMessage.success('创建成功，合同已发送给租户确认')
            this.dialogVisible = false
            this.loadData()
          } catch (e) { console.error(e) }
        }
      })
    },
    formatMoney(v) { return v ? parseFloat(v).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) : '-' },
    getStatusType(s) { return { '待确认': 'info', '生效中': 'success', '已到期': 'warning', '已终止': 'danger' }[s] || '' },
    getSubletStatusType(s) { return { '无': '', '待确认': 'warning', '已转租': 'success', '已拒绝': 'danger' }[s] || 'info' }
  }
}
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
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
