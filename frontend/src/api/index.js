import request from '../utils/request'

export function login(data) {
  return request({
    url: '/auth/login',
    method: 'post',
    data
  })
}

export function register(data) {
  return request({
    url: '/auth/register',
    method: 'post',
    data
  })
}

export function getUserInfo() {
  return request({
    url: '/auth/info',
    method: 'get'
  })
}

export function getUsers() {
  return request({
    url: '/users',
    method: 'get'
  })
}

export function getUser(id) {
  return request({
    url: `/users/${id}`,
    method: 'get'
  })
}

export function createUser(data) {
  return request({
    url: '/users',
    method: 'post',
    data
  })
}

export function updateUser(id, data) {
  return request({
    url: `/users/${id}`,
    method: 'put',
    data
  })
}

export function deleteUser(id) {
  return request({
    url: `/users/${id}`,
    method: 'delete'
  })
}

export function getApartments() {
  return request({
    url: '/apartments',
    method: 'get'
  })
}

export function getApartment(id) {
  return request({
    url: `/apartments/${id}`,
    method: 'get'
  })
}

export function getApartmentsByLandlord(landlordId) {
  return request({
    url: `/apartments/landlord/${landlordId}`,
    method: 'get'
  })
}

export function getApartmentsByStatus(status) {
  return request({
    url: `/apartments/status/${status}`,
    method: 'get'
  })
}

export function createApartment(data) {
  return request({
    url: '/apartments',
    method: 'post',
    data
  })
}

export function updateApartment(id, data) {
  return request({
    url: `/apartments/${id}`,
    method: 'put',
    data
  })
}

export function deleteApartment(id) {
  return request({
    url: `/apartments/${id}`,
    method: 'delete'
  })
}

export function getAuditedApartments() {
  return request({
    url: '/apartments/audited',
    method: 'get'
  })
}

export function getPendingAuditApartments() {
  return request({
    url: '/apartments/pending-audit',
    method: 'get'
  })
}

export function auditApartment(id, status, remark) {
  return request({
    url: `/apartments/${id}/audit`,
    method: 'put',
    params: { status, remark }
  })
}

export function getAppointments() {
  return request({
    url: '/appointments',
    method: 'get'
  })
}

export function getAppointment(id) {
  return request({
    url: `/appointments/${id}`,
    method: 'get'
  })
}

export function getAppointmentsByTenant(tenantId) {
  return request({
    url: `/appointments/tenant/${tenantId}`,
    method: 'get'
  })
}

export function getAppointmentsByLandlord(landlordId) {
  return request({
    url: `/appointments/landlord/${landlordId}`,
    method: 'get'
  })
}

export function createAppointment(data) {
  return request({
    url: '/appointments',
    method: 'post',
    data
  })
}

export function updateAppointment(id, data) {
  return request({
    url: `/appointments/${id}`,
    method: 'put',
    data
  })
}

export function handleAppointment(id, status, reply) {
  return request({
    url: `/appointments/${id}/handle`,
    method: 'put',
    params: { status, reply }
  })
}

export function deleteAppointment(id) {
  return request({
    url: `/appointments/${id}`,
    method: 'delete'
  })
}

export function getAcceptedTenantsByLandlord(landlordId) {
  return request({
    url: `/appointments/landlord/${landlordId}/accepted-tenants`,
    method: 'get'
  })
}

export function getContracts() {
  return request({
    url: '/contracts',
    method: 'get'
  })
}

export function getContract(id) {
  return request({
    url: `/contracts/${id}`,
    method: 'get'
  })
}

export function getContractsByTenant(tenantId) {
  return request({
    url: `/contracts/tenant/${tenantId}`,
    method: 'get'
  })
}

export function getContractsByLandlord(landlordId) {
  return request({
    url: `/contracts/landlord/${landlordId}`,
    method: 'get'
  })
}

export function getContractsByApartment(apartmentId) {
  return request({
    url: `/contracts/apartment/${apartmentId}`,
    method: 'get'
  })
}

export function createContract(data) {
  return request({
    url: '/contracts',
    method: 'post',
    data
  })
}

export function updateContract(id, data) {
  return request({
    url: `/contracts/${id}`,
    method: 'put',
    data
  })
}

export function deleteContract(id) {
  return request({
    url: `/contracts/${id}`,
    method: 'delete'
  })
}

export function terminateContract(id, reason) {
  return request({
    url: `/contracts/${id}/terminate`,
    method: 'put',
    params: { reason }
  })
}

export function requestSublet(id, newTenantId) {
  return request({
    url: `/contracts/${id}/sublet`,
    method: 'put',
    params: { newTenantId }
  })
}

export function confirmSublet(id) {
  return request({
    url: `/contracts/${id}/sublet/confirm`,
    method: 'put'
  })
}

export function rejectSublet(id) {
  return request({
    url: `/contracts/${id}/sublet/reject`,
    method: 'put'
  })
}

export function getPayments() {
  return request({
    url: '/payments',
    method: 'get'
  })
}

export function getPayment(id) {
  return request({
    url: `/payments/${id}`,
    method: 'get'
  })
}

export function getPaymentsByContract(contractId) {
  return request({
    url: `/payments/contract/${contractId}`,
    method: 'get'
  })
}

export function getPaymentsByTenant(tenantId) {
  return request({
    url: `/payments/tenant/${tenantId}`,
    method: 'get'
  })
}

export function getPaymentsByLandlord(landlordId) {
  return request({
    url: `/payments/landlord/${landlordId}`,
    method: 'get'
  })
}

export function createPayment(data) {
  return request({
    url: '/payments',
    method: 'post',
    data
  })
}

export function updatePayment(id, data) {
  return request({
    url: `/payments/${id}`,
    method: 'put',
    data
  })
}

export function deletePayment(id) {
  return request({
    url: `/payments/${id}`,
    method: 'delete'
  })
}

export function getRepairs() {
  return request({
    url: '/repairs',
    method: 'get'
  })
}

export function getRepair(id) {
  return request({
    url: `/repairs/${id}`,
    method: 'get'
  })
}

export function getRepairsByTenant(tenantId) {
  return request({
    url: `/repairs/tenant/${tenantId}`,
    method: 'get'
  })
}

export function getRepairsByLandlord(landlordId) {
  return request({
    url: `/repairs/landlord/${landlordId}`,
    method: 'get'
  })
}

export function createRepair(data) {
  return request({
    url: '/repairs',
    method: 'post',
    data
  })
}

export function updateRepair(id, data) {
  return request({
    url: `/repairs/${id}`,
    method: 'put',
    data
  })
}

export function handleRepair(id, status, reply) {
  return request({
    url: `/repairs/${id}/handle`,
    method: 'put',
    params: { status, reply }
  })
}

export function deleteRepair(id) {
  return request({
    url: `/repairs/${id}`,
    method: 'delete'
  })
}

export function getMessages() {
  return request({
    url: '/messages',
    method: 'get'
  })
}

export function getMessage(id) {
  return request({
    url: `/messages/${id}`,
    method: 'get'
  })
}

export function getMessagesByReceiver(receiverId) {
  return request({
    url: `/messages/receiver/${receiverId}`,
    method: 'get'
  })
}

export function getMessagesBySender(senderId) {
  return request({
    url: `/messages/sender/${senderId}`,
    method: 'get'
  })
}

export function getAnnouncements(role) {
  return request({
    url: '/messages/announcements',
    method: 'get',
    params: { role }
  })
}

export function createMessage(data) {
  return request({
    url: '/messages',
    method: 'post',
    data
  })
}

export function markMessageAsRead(id) {
  return request({
    url: `/messages/${id}/read`,
    method: 'put'
  })
}

export function deleteMessage(id) {
  return request({
    url: `/messages/${id}`,
    method: 'delete'
  })
}

export function uploadFile(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: '/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export function getFavorites(tenantId) {
  return request({ url: `/favorites/tenant/${tenantId}`, method: 'get' })
}

export function checkFavorite(tenantId, apartmentId) {
  return request({ url: '/favorites/check', method: 'get', params: { tenantId, apartmentId } })
}

export function addFavorite(data) {
  return request({ url: '/favorites', method: 'post', data })
}

export function removeFavorite(tenantId, apartmentId) {
  return request({ url: '/favorites', method: 'delete', params: { tenantId, apartmentId } })
}

export function getReviews() {
  return request({ url: '/reviews', method: 'get' })
}

export function getApartmentReviews(apartmentId) {
  return request({ url: `/reviews/apartment/${apartmentId}`, method: 'get' })
}

export function getApprovedApartmentReviews(apartmentId) {
  return request({ url: `/reviews/apartment/${apartmentId}/approved`, method: 'get' })
}

export function getTenantReviews(tenantId) {
  return request({ url: `/reviews/tenant/${tenantId}`, method: 'get' })
}

export function getLandlordReviews(landlordId) {
  return request({ url: `/reviews/landlord/${landlordId}`, method: 'get' })
}

export function createReview(data) {
  return request({ url: '/reviews', method: 'post', data })
}

export function auditReview(id, status, remark) {
  return request({ url: `/reviews/${id}/audit`, method: 'put', params: { status, remark } })
}

export function replyReview(id, reply) {
  return request({ url: `/reviews/${id}/reply`, method: 'post', data: { reply } })
}

export function deleteReview(id, tenantId) {
  return request({ url: `/reviews/${id}/tenant/${tenantId}`, method: 'delete' })
}

export function getComplaints(tenantId) {
  return request({ url: `/complaints/tenant/${tenantId}`, method: 'get' })
}

export function getAllComplaints() {
  return request({ url: '/complaints', method: 'get' })
}

export function createComplaint(data) {
  return request({ url: '/complaints', method: 'post', data })
}

export function replyComplaint(id, reply) {
  return request({ url: `/complaints/${id}/reply`, method: 'post', data: { reply } })
}

export function getLandlordStatistics(landlordId) {
  return request({ url: `/statistics/landlord/${landlordId}`, method: 'get' })
}

export function getAdminStatistics() {
  return request({ url: '/statistics/admin', method: 'get' })
}
