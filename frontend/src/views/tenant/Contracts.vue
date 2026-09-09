<template>
  <div class="contracts">
    <el-card>
      <template #header><span>我的合同</span></template>
      <el-table :data="contracts" v-loading="loading" stripe>
        <el-table-column prop="contractNo" label="合同编号" min-width="150" />
        <el-table-column label="公寓" min-width="120">
          <template #default="scope">
            <div>ID:{{ scope.row.apartment?.id }}</div>
            <div style="color: #909399; font-size: 12px;">{{ scope.row.apartment?.name || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="房东" min-width="120">
          <template #default="scope">
            <div>ID:{{ scope.row.landlord?.id }}</div>
            <div style="color: #909399; font-size: 12px;">{{ scope.row.landlord?.realName || '-' }}</div>
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
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="scope">
            <el-button size="small" link @click="handleView(scope.row)">查看</el-button>
            <el-button size="small" type="success" link @click="handleConfirm(scope.row)" v-if="scope.row.status === '待确认'">确认</el-button>
            <el-button size="small" type="warning" link @click="handleRenew(scope.row)" v-if="scope.row.status === '生效中' && scope.row.subletStatus === '无'">续租</el-button>
            <el-button size="small" type="danger" link @click="handleTerminate(scope.row)" v-if="scope.row.status === '生效中' && scope.row.subletStatus === '无'">解约</el-button>
            <el-button size="small" type="primary" link @click="handleSublet(scope.row)" v-if="scope.row.status === '生效中' && scope.row.subletStatus === '无'">转租</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="合同详情" width="700px">
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
        <p><strong>房屋面积：</strong>{{ currentContract.apartment?.area || '-' }} 平方米</p>
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
        <el-button @click="dialogVisible = false">关闭</el-button>
        <el-button type="success" @click="handleConfirm(currentContract)" v-if="currentContract?.status === '待确认'">确认合同</el-button>
        <el-button type="warning" @click="handleRenew(currentContract)" v-if="currentContract?.status === '生效中' && currentContract?.subletStatus === '无'">申请续租</el-button>
        <el-button type="danger" @click="handleTerminate(currentContract)" v-if="currentContract?.status === '生效中' && currentContract?.subletStatus === '无'">申请解约</el-button>
        <el-button type="primary" @click="handleSublet(currentContract)" v-if="currentContract?.status === '生效中' && currentContract?.subletStatus === '无'">申请转租</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="renewDialogVisible" title="申请续租" width="500px">
      <el-form :model="renewForm" :rules="renewRules" ref="renewFormRef" label-width="100px">
        <el-form-item label="原合同">
          <el-input :value="currentContract?.contractNo" disabled />
        </el-form-item>
        <el-form-item label="原结束日期">
          <el-input :value="currentContract?.endDate" disabled />
        </el-form-item>
        <el-form-item label="续租开始日期">
          <el-input :value="currentContract?.endDate" disabled />
          <div style="color: #909399; font-size: 12px;">续租从原合同结束日期开始</div>
        </el-form-item>
        <el-form-item label="续租结束日期" prop="newEndDate">
          <el-date-picker v-model="renewForm.newEndDate" type="date" placeholder="选择续租结束日期" style="width: 100%" value-format="YYYY-MM-DD" :disabled-date="disabledDate" />
        </el-form-item>
        <el-form-item label="月租(元)">
          <el-input-number v-model="renewForm.monthlyRent" :min="0" :precision="2" style="width: 100%" />
          <div style="color: #909399; font-size: 12px;">默认为原合同月租，可协商修改</div>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="renewForm.remark" type="textarea" :rows="2" placeholder="请输入续租备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="renewDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRenew">提交续租申请</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="terminateDialogVisible" title="申请解约" width="400px">
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

    <el-dialog v-model="subletDialogVisible" title="申请转租" width="500px">
      <el-form :model="subletForm" :rules="subletRules" ref="subletFormRef" label-width="100px">
        <el-form-item label="原合同">
          <el-input :value="currentContract?.contractNo" disabled />
        </el-form-item>
        <el-form-item label="新租户ID" prop="newTenantId">
          <el-select v-model="subletForm.newTenantId" placeholder="请选择新租户" style="width: 100%" filterable>
            <el-option v-for="item in tenants" :key="item.id" :label="`ID:${item.id} - ${item.realName}`" :value="item.id">
              <span>ID:{{ item.id }} - {{ item.realName }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-alert type="warning" :closable="false" style="margin-top: 10px;">
          <template #title>转租需要房东确认后才能生效，请确保新租户已同意接手。</template>
        </el-alert>
      </el-form>
      <template #footer>
        <el-button @click="subletDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmSublet">提交转租申请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { getContractsByTenant, createContract, updateContract, terminateContract, requestSublet, getUsers } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'TenantContracts',
  data() {
    return {
      contracts: [],
      tenants: [],
      loading: false,
      dialogVisible: false,
      renewDialogVisible: false,
      terminateDialogVisible: false,
      subletDialogVisible: false,
      currentContract: null,
      renewForm: { newEndDate: '', monthlyRent: 0, remark: '' },
      renewRules: { newEndDate: [{ required: true, message: '请选择续租结束日期', trigger: 'change' }] },
      terminateForm: { reason: '' },
      subletForm: { newTenantId: null },
      subletRules: { newTenantId: [{ required: true, message: '请选择新租户', trigger: 'change' }] }
    }
  },
  created() { this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const userId = localStorage.getItem('userId')
        const [contracts, users] = await Promise.all([
          getContractsByTenant(userId),
          getUsers()
        ])
        this.contracts = contracts.data
        this.tenants = users.data.filter(u => u.role === 'TENANT')
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    handleView(contract) {
      this.currentContract = contract
      this.dialogVisible = true
    },
    handleConfirm(contract) {
      ElMessageBox.confirm('确认接受此合同吗？确认后合同将正式生效。', '确认合同', {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        await updateContract(contract.id, { ...contract, status: '生效中' })
        ElMessage.success('合同已确认生效')
        this.dialogVisible = false
        this.loadData()
      }).catch(() => {})
    },
    handleRenew(contract) {
      this.currentContract = contract
      this.renewForm = { newEndDate: '', monthlyRent: contract.monthlyRent, remark: '' }
      this.renewDialogVisible = true
    },
    disabledDate(date) {
      if (!this.currentContract?.endDate) return false
      const endDate = new Date(this.currentContract.endDate)
      return date <= endDate
    },
    async submitRenew() {
      this.$refs.renewFormRef.validate(async (valid) => {
        if (valid) {
          try {
            const userId = localStorage.getItem('userId')
            const newContract = {
              apartment: { id: this.currentContract.apartment.id },
              tenant: { id: userId },
              landlord: { id: this.currentContract.landlord.id },
              startDate: this.currentContract.endDate,
              endDate: this.renewForm.newEndDate,
              monthlyRent: this.renewForm.monthlyRent,
              deposit: this.currentContract.deposit,
              paymentMethod: this.currentContract.paymentMethod,
              status: '待确认',
              contractType: '续租',
              originalContractId: this.currentContract.id,
              remark: this.renewForm.remark
            }
            await createContract(newContract)
            ElMessage.success('续租申请已提交，等待房东确认')
            this.renewDialogVisible = false
            this.dialogVisible = false
            this.loadData()
          } catch (e) { console.error(e) }
        }
      })
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
        this.dialogVisible = false
        this.loadData()
      } catch (e) {
        ElMessage.error(e.response?.data?.message || '解约失败')
      }
    },
    handleSublet(contract) {
      this.currentContract = contract
      this.subletForm = { newTenantId: null }
      this.subletDialogVisible = true
    },
    async confirmSublet() {
      this.$refs.subletFormRef.validate(async (valid) => {
        if (valid) {
          try {
            await requestSublet(this.currentContract.id, this.subletForm.newTenantId)
            ElMessage.success('转租申请已提交，等待房东确认')
            this.subletDialogVisible = false
            this.dialogVisible = false
            this.loadData()
          } catch (e) {
            ElMessage.error(e.response?.data?.message || '转租申请失败')
          }
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
