import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import AdminLayout from '../views/admin/Layout.vue'
import LandlordLayout from '../views/landlord/Layout.vue'
import TenantLayout from '../views/tenant/Layout.vue'

const routes = [
  { path: '/login', name: 'Login', component: Login },
  {
    path: '/admin',
    component: AdminLayout,
    meta: { role: 'ADMIN' },
    children: [
      { path: '', redirect: '/admin/dashboard' },
      { path: 'dashboard', name: 'AdminDashboard', component: () => import('../views/admin/Dashboard.vue') },
      { path: 'users', name: 'AdminUsers', component: () => import('../views/admin/Users.vue') },
      { path: 'apartments', name: 'AdminApartments', component: () => import('../views/admin/Apartments.vue') },
      { path: 'contracts', name: 'AdminContracts', component: () => import('../views/admin/Contracts.vue') },
      { path: 'reviews', name: 'AdminReviews', component: () => import('../views/admin/Reviews.vue') },
      { path: 'complaints', name: 'AdminComplaints', component: () => import('../views/admin/Complaints.vue') },
      { path: 'statistics', name: 'AdminStatistics', component: () => import('../views/admin/Statistics.vue') },
      { path: 'messages', name: 'AdminMessages', component: () => import('../views/admin/Messages.vue') }
    ]
  },
  {
    path: '/landlord',
    component: LandlordLayout,
    meta: { role: 'LANDLORD' },
    children: [
      { path: '', redirect: '/landlord/apartments' },
      { path: 'apartments', name: 'LandlordApartments', component: () => import('../views/landlord/Apartments.vue') },
      { path: 'appointments', name: 'LandlordAppointments', component: () => import('../views/landlord/Appointments.vue') },
      { path: 'contracts', name: 'LandlordContracts', component: () => import('../views/landlord/Contracts.vue') },
      { path: 'payments', name: 'LandlordPayments', component: () => import('../views/landlord/Payments.vue') },
      { path: 'repairs', name: 'LandlordRepairs', component: () => import('../views/landlord/Repairs.vue') },
      { path: 'messages', name: 'LandlordMessages', component: () => import('../views/landlord/Messages.vue') },
      { path: 'statistics', name: 'LandlordStatistics', component: () => import('../views/landlord/Statistics.vue') },
      { path: 'profile', name: 'LandlordProfile', component: () => import('../views/landlord/Profile.vue') }
    ]
  },
  {
    path: '/tenant',
    component: TenantLayout,
    meta: { role: 'TENANT' },
    children: [
      { path: '', redirect: '/tenant/apartments' },
      { path: 'apartments', name: 'TenantApartments', component: () => import('../views/tenant/Apartments.vue') },
      { path: 'favorites', name: 'TenantFavorites', component: () => import('../views/tenant/Favorites.vue') },
      { path: 'appointments', name: 'TenantAppointments', component: () => import('../views/tenant/Appointments.vue') },
      { path: 'contracts', name: 'TenantContracts', component: () => import('../views/tenant/Contracts.vue') },
      { path: 'payments', name: 'TenantPayments', component: () => import('../views/tenant/Payments.vue') },
      { path: 'repairs', name: 'TenantRepairs', component: () => import('../views/tenant/Repairs.vue') },
      { path: 'messages', name: 'TenantMessages', component: () => import('../views/tenant/Messages.vue') },
      { path: 'profile', name: 'TenantProfile', component: () => import('../views/tenant/Profile.vue') }
    ]
  },
  { path: '/', redirect: '/login' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const role = localStorage.getItem('role')

  if (to.path !== '/login' && !token) {
    next('/login')
  } else if (to.meta.role && to.meta.role !== role) {
    if (role === 'ADMIN') next('/admin/dashboard')
    else if (role === 'LANDLORD') next('/landlord/apartments')
    else if (role === 'TENANT') next('/tenant/apartments')
    else next('/login')
  } else {
    next()
  }
})

export default router
