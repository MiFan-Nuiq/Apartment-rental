<template>
  <div class="login-wrapper" @mousemove="handleMouseMove">
    <div class="login-container">
      <!-- Left Content Section -->
      <div class="left-section">
        <div class="brand-logo">
          <div class="logo-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
            </svg>
          </div>
          <span>公寓租赁管理系统</span>
        </div>

        <div class="characters-container">
          <div class="characters-wrapper">
            <!-- Purple character -->
            <div 
              class="character purple"
              :class="{ jumping: isPurpleJumping, waving: isPurpleWaving }"
              :style="{
                height: (isTyping || (loginForm.password.length > 0 && !showPassword)) ? '300px' : '280px',
                transform: (loginForm.password.length > 0 && showPassword)
                  ? 'skewX(0deg)'
                  : (isTyping || (loginForm.password.length > 0 && !showPassword))
                    ? `skewX(${purplePos.bodySkew - 12}deg) translateX(30px)` 
                    : `skewX(${purplePos.bodySkew}deg)`
              }"
            >
              <div class="eyes" :style="{ left: (loginForm.password.length > 0 && showPassword) ? '15px' : `${32 + purplePos.faceX}px`, top: (loginForm.password.length > 0 && showPassword) ? '25px' : `${28 + purplePos.faceY}px` }">
                <div class="eye" :class="{ blinking: isPurpleBlinking }">
                  <div class="pupil" :style="{ transform: `translate(${purplePupilX}px, ${purplePupilY}px)` }"></div>
                </div>
                <div class="eye" :class="{ blinking: isPurpleBlinking }">
                  <div class="pupil" :style="{ transform: `translate(${purplePupilX}px, ${purplePupilY}px)` }"></div>
                </div>
              </div>
              <div class="arm left" :class="{ waving: isPurpleWaving }"></div>
            </div>

            <!-- Black character -->
            <div 
              class="character black"
              :class="{ jumping: isBlackJumping, bouncing: isBlackBouncing }"
              :style="{
                transform: (loginForm.password.length > 0 && showPassword)
                  ? 'skewX(0deg)'
                  : isLookingAtEachOther
                    ? `skewX(${blackPos.bodySkew * 1.5 + 8}deg) translateX(15px)`
                    : (isTyping || (loginForm.password.length > 0 && !showPassword))
                      ? `skewX(${blackPos.bodySkew * 1.5}deg)` 
                      : `skewX(${blackPos.bodySkew}deg)`
              }"
            >
              <div class="eyes" :style="{ left: (loginForm.password.length > 0 && showPassword) ? '8px' : `${18 + blackPos.faceX}px`, top: (loginForm.password.length > 0 && showPassword) ? '20px' : `${24 + blackPos.faceY}px` }">
                <div class="eye small" :class="{ blinking: isBlackBlinking }">
                  <div class="pupil small" :style="{ transform: `translate(${blackPupilX}px, ${blackPupilY}px)` }"></div>
                </div>
                <div class="eye small" :class="{ blinking: isBlackBlinking }">
                  <div class="pupil small" :style="{ transform: `translate(${blackPupilX}px, ${blackPupilY}px)` }"></div>
                </div>
              </div>
            </div>

            <!-- Orange character -->
            <div 
              class="character orange"
              :class="{ swaying: isOrangeSwaying }"
              :style="{ transform: (loginForm.password.length > 0 && showPassword) ? 'skewX(0deg)' : `skewX(${orangePos.bodySkew}deg)` }"
            >
              <div class="pupil-eyes" :style="{ left: (loginForm.password.length > 0 && showPassword) ? '35px' : `${58 + orangePos.faceX}px`, top: (loginForm.password.length > 0 && showPassword) ? '60px' : `${62 + orangePos.faceY}px` }">
                <div class="pupil-only" :style="{ transform: `translate(${orangePupilX}px, ${orangePupilY}px)` }"></div>
                <div class="pupil-only" :style="{ transform: `translate(${orangePupilX}px, ${orangePupilY}px)` }"></div>
              </div>
            </div>

            <!-- Yellow character -->
            <div 
              class="character yellow"
              :class="{ jumping: isYellowJumping, happy: isYellowHappy }"
              :style="{ transform: (loginForm.password.length > 0 && showPassword) ? 'skewX(0deg)' : `skewX(${yellowPos.bodySkew}deg)` }"
            >
              <div class="pupil-eyes" :style="{ left: (loginForm.password.length > 0 && showPassword) ? '15px' : `${36 + yellowPos.faceX}px`, top: (loginForm.password.length > 0 && showPassword) ? '25px' : `${28 + yellowPos.faceY}px` }">
                <div class="pupil-only" :style="{ transform: `translate(${yellowPupilX}px, ${yellowPupilY}px)` }"></div>
                <div class="pupil-only" :style="{ transform: `translate(${yellowPupilX}px, ${yellowPupilY}px)` }"></div>
              </div>
              <div class="mouth" :class="{ happy: isYellowHappy }" :style="{ left: (loginForm.password.length > 0 && showPassword) ? '8px' : `${28 + yellowPos.faceX}px`, top: (loginForm.password.length > 0 && showPassword) ? '60px' : `${60 + yellowPos.faceY}px` }"></div>
            </div>
          </div>
        </div>

        <div class="footer-links">
          <a href="#">隐私政策</a>
          <a href="#">服务条款</a>
          <a href="#">联系我们</a>
        </div>

        <div class="bg-grid"></div>
      </div>

      <!-- Right Login Section -->
      <div class="right-section">
        <div class="form-container">
          <div class="form-header">
            <h1>{{ activeTab === 'login' ? '欢迎回来!' : '创建账户' }}</h1>
            <p>{{ activeTab === 'login' ? '请输入您的登录信息' : '请填写注册信息' }}</p>
          </div>

          <!-- Tab Switcher -->
          <div class="tab-switcher">
            <button :class="{ active: activeTab === 'login' }" @click="activeTab = 'login'">登录</button>
            <button :class="{ active: activeTab === 'register' }" @click="activeTab = 'register'">注册</button>
          </div>

          <!-- Login Form -->
          <form v-if="activeTab === 'login'" @submit.prevent="handleLogin" class="login-form">
            <div class="form-group">
              <label>用户名</label>
              <input 
                type="text" 
                v-model="loginForm.username" 
                placeholder="请输入用户名"
                @focus="isTyping = true"
                @blur="isTyping = false"
                required
              />
            </div>

            <div class="form-group">
              <label>密码</label>
              <div class="password-input">
                <input 
                  :type="showPassword ? 'text' : 'password'" 
                  v-model="loginForm.password" 
                  placeholder="••••••••"
                  @keyup.enter="handleLogin"
                  required
                />
                <button type="button" class="toggle-password" @click="showPassword = !showPassword">
                  <svg v-if="showPassword" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" x2="22" y1="2" y2="22"/>
                  </svg>
                  <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>
                  </svg>
                </button>
              </div>
            </div>

            <div v-if="errorMsg" class="error-message">{{ errorMsg }}</div>

            <button type="submit" class="submit-btn" :disabled="loading">
              {{ loading ? '登录中...' : '登录' }}
            </button>
          </form>

          <!-- Register Form -->
          <form v-else @submit.prevent="handleRegister" class="login-form">
            <div class="form-group">
              <label>用户名</label>
              <input type="text" v-model="registerForm.username" placeholder="请输入用户名" required />
            </div>

            <div class="form-group">
              <label>密码</label>
              <input type="password" v-model="registerForm.password" placeholder="请输入密码" required />
            </div>

            <div class="form-group">
              <label>确认密码</label>
              <input type="password" v-model="registerForm.confirmPassword" placeholder="请确认密码" required />
            </div>

            <div class="form-row">
              <div class="form-group half">
                <label>真实姓名</label>
                <input type="text" v-model="registerForm.realName" placeholder="请输入姓名" required />
              </div>
              <div class="form-group half">
                <label>手机号码</label>
                <input type="tel" v-model="registerForm.phone" placeholder="请输入手机号" required />
              </div>
            </div>

            <div class="form-group">
              <label>选择角色</label>
              <div class="role-selector">
                <label class="role-option" :class="{ selected: registerForm.role === 'LANDLORD' }">
                  <input type="radio" value="LANDLORD" v-model="registerForm.role" />
                  <span class="role-icon">🏠</span>
                  <span class="role-text">房东</span>
                </label>
                <label class="role-option" :class="{ selected: registerForm.role === 'TENANT' }">
                  <input type="radio" value="TENANT" v-model="registerForm.role" />
                  <span class="role-icon">👤</span>
                  <span class="role-text">租户</span>
                </label>
              </div>
            </div>

            <div v-if="errorMsg" class="error-message">{{ errorMsg }}</div>

            <button type="submit" class="submit-btn" :disabled="loading">
              {{ loading ? '注册中...' : '注册' }}
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { login, register } from '../api'
import { ElMessage } from 'element-plus'

export default {
  name: 'Login',
  data() {
    return {
      activeTab: 'login',
      loginForm: { username: '', password: '' },
      registerForm: { username: '', password: '', confirmPassword: '', realName: '', phone: '', role: 'TENANT' },
      showPassword: false,
      loading: false,
      errorMsg: '',
      mouseX: 0,
      mouseY: 0,
      isTyping: false,
      isPurpleBlinking: false,
      isBlackBlinking: false,
      isLookingAtEachOther: false,
      purplePupilX: 0,
      purplePupilY: 0,
      blackPupilX: 0,
      blackPupilY: 0,
      orangePupilX: 0,
      orangePupilY: 0,
      yellowPupilX: 0,
      yellowPupilY: 0,
      isPurpleJumping: false,
      isBlackJumping: false,
      isYellowJumping: false,
      isPurpleWaving: false,
      isBlackBouncing: false,
      isOrangeSwaying: false,
      isYellowHappy: false
    }
  },
  computed: {
    purplePos() {
      return this.calculatePosition(50, 130)
    },
    blackPos() {
      return this.calculatePosition(180, 110)
    },
    orangePos() {
      return this.calculatePosition(0, 70)
    },
    yellowPos() {
      return this.calculatePosition(230, 80)
    }
  },
  mounted() {
    this.startBlinking()
    this.startAnimations()
  },
  methods: {
    handleMouseMove(e) {
      this.mouseX = e.clientX
      this.mouseY = e.clientY
      this.updatePupils()
    },
    calculatePosition(baseX, baseY) {
      const deltaX = this.mouseX - (window.innerWidth / 2 + baseX)
      const deltaY = this.mouseY - (window.innerHeight / 2 + baseY)
      const faceX = Math.max(-15, Math.min(15, deltaX / 15))
      const faceY = Math.max(-10, Math.min(10, deltaY / 20))
      const bodySkew = Math.max(-6, Math.min(6, -deltaX / 80))
      return { faceX, faceY, bodySkew }
    },
    updatePupils() {
      const forceLook = this.loginForm.password.length > 0 && this.showPassword
      this.purplePupilX = forceLook ? -3 : Math.max(-4, Math.min(4, (this.mouseX - window.innerWidth / 2) / 80))
      this.purplePupilY = forceLook ? -3 : Math.max(-4, Math.min(4, (this.mouseY - window.innerHeight / 2) / 80))
      this.blackPupilX = forceLook ? -3 : Math.max(-3, Math.min(3, (this.mouseX - window.innerWidth / 2) / 100))
      this.blackPupilY = forceLook ? -3 : Math.max(-3, Math.min(3, (this.mouseY - window.innerHeight / 2) / 100))
      this.orangePupilX = forceLook ? -4 : Math.max(-4, Math.min(4, (this.mouseX - window.innerWidth / 2) / 80))
      this.orangePupilY = forceLook ? -3 : Math.max(-4, Math.min(4, (this.mouseY - window.innerHeight / 2) / 80))
      this.yellowPupilX = forceLook ? -4 : Math.max(-4, Math.min(4, (this.mouseX - window.innerWidth / 2) / 80))
      this.yellowPupilY = forceLook ? -3 : Math.max(-4, Math.min(4, (this.mouseY - window.innerHeight / 2) / 80))
    },
    startBlinking() {
      const schedulePurpleBlink = () => {
        setTimeout(() => {
          this.isPurpleBlinking = true
          setTimeout(() => {
            this.isPurpleBlinking = false
            schedulePurpleBlink()
          }, 100)
        }, Math.random() * 3000 + 2000)
      }
      const scheduleBlackBlink = () => {
        setTimeout(() => {
          this.isBlackBlinking = true
          setTimeout(() => {
            this.isBlackBlinking = false
            scheduleBlackBlink()
          }, 100)
        }, Math.random() * 3000 + 2000)
      }
      schedulePurpleBlink()
      scheduleBlackBlink()
    },
    startAnimations() {
      setInterval(() => {
        const action = Math.floor(Math.random() * 6)
        switch(action) {
          case 0:
            this.isPurpleJumping = true
            setTimeout(() => { this.isPurpleJumping = false }, 400)
            break
          case 1:
            this.isBlackJumping = true
            setTimeout(() => { this.isBlackJumping = false }, 400)
            break
          case 2:
            this.isYellowJumping = true
            setTimeout(() => { this.isYellowJumping = false }, 400)
            break
          case 3:
            this.isPurpleWaving = true
            setTimeout(() => { this.isPurpleWaving = false }, 600)
            break
          case 4:
            this.isOrangeSwaying = true
            setTimeout(() => { this.isOrangeSwaying = false }, 500)
            break
          case 5:
            this.isYellowHappy = true
            setTimeout(() => { this.isYellowHappy = false }, 800)
            break
        }
      }, 2000)
    },
    handleLogin() {
      if (!this.loginForm.username || !this.loginForm.password) {
        this.errorMsg = '请填写用户名和密码'
        return
      }
      this.loading = true
      this.errorMsg = ''
      login(this.loginForm).then(res => {
        this.saveUserInfo(res.data)
        ElMessage.success('登录成功')
        this.redirectByRole(res.data.role)
      }).catch(() => {
        this.errorMsg = '用户名或密码错误'
      }).finally(() => {
        this.loading = false
      })
    },
    handleRegister() {
      if (this.registerForm.password !== this.registerForm.confirmPassword) {
        this.errorMsg = '两次输入的密码不一致'
        return
      }
      if (!/^1[3-9]\d{9}$/.test(this.registerForm.phone)) {
        this.errorMsg = '请输入正确的手机号码'
        return
      }
      this.loading = true
      this.errorMsg = ''
      register(this.registerForm).then(res => {
        this.saveUserInfo(res.data)
        ElMessage.success('注册成功')
        this.redirectByRole(res.data.role)
      }).catch(e => {
        this.errorMsg = e.response?.data?.message || '注册失败'
      }).finally(() => {
        this.loading = false
      })
    },
    saveUserInfo(data) {
      localStorage.setItem('token', data.token)
      localStorage.setItem('username', data.username)
      localStorage.setItem('realName', data.realName)
      localStorage.setItem('role', data.role)
      localStorage.setItem('userId', data.userId)
    },
    redirectByRole(role) {
      const routes = { 'ADMIN': '/admin/dashboard', 'LANDLORD': '/landlord/apartments', 'TENANT': '/tenant/apartments' }
      this.$router.push(routes[role] || '/login')
    }
  }
}
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.login-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1a1a1a;
  padding: 20px;
}

.login-container {
  width: 100%;
  max-width: 1000px;
  background: #2d2d2d;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: 600px;
}

@media (max-width: 900px) {
  .login-container {
    grid-template-columns: 1fr;
  }
  .left-section {
    display: none !important;
  }
}

/* Left Section */
.left-section {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  background: #d8d8d8;
  padding: 40px;
  color: #333;
}

.brand-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  position: relative;
  z-index: 20;
}

.logo-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(0,0,0,0.1);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Characters */
.characters-container {
  position: relative;
  z-index: 20;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  height: 350px;
}

.characters-wrapper {
  position: relative;
  width: 400px;
  height: 280px;
}

.character {
  position: absolute;
  bottom: 0;
  transition: all 0.15s ease-out;
  transform-origin: bottom center;
}

.character.jumping {
  animation: jump 0.4s ease-out;
}

.character.waving .arm {
  animation: wave 0.6s ease-in-out;
}

.character.bouncing {
  animation: bounce 0.5s ease-out;
}

.character.swaying {
  animation: sway 0.5s ease-in-out;
}

.character.happy {
  animation: happy 0.8s ease-in-out;
}

@keyframes jump {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-30px); }
}

@keyframes wave {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-30deg); }
  75% { transform: rotate(30deg); }
}

@keyframes bounce {
  0%, 100% { transform: scaleY(1); }
  50% { transform: scaleY(0.9) scaleX(1.1); }
}

@keyframes sway {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-5deg); }
  75% { transform: rotate(5deg); }
}

@keyframes happy {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.character.purple {
  left: 50px;
  width: 130px;
  background-color: #6C3FF5;
  border-radius: 10px 10px 0 0;
  z-index: 1;
}

.character.black {
  left: 180px;
  width: 90px;
  height: 220px;
  background-color: #4a4a4a;
  border-radius: 8px 8px 0 0;
  z-index: 2;
}

.character.orange {
  left: 0px;
  width: 170px;
  height: 140px;
  background-color: #FF9B6B;
  border-radius: 85px 85px 0 0;
  z-index: 3;
}

.character.yellow {
  left: 230px;
  width: 100px;
  height: 160px;
  background-color: #E8D754;
  border-radius: 50px 50px 0 0;
  z-index: 4;
}

.eyes {
  position: absolute;
  display: flex;
  gap: 24px;
  transition: all 0.1s ease-out;
}

.eye {
  width: 14px;
  height: 14px;
  background-color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  transition: all 0.1s ease;
}

.eye.small {
  width: 12px;
  height: 12px;
}

.eye.blinking {
  height: 2px;
}

.pupil {
  width: 5px;
  height: 5px;
  background-color: #2D2D2D;
  border-radius: 50%;
  transition: transform 0.05s ease-out;
}

.pupil.small {
  width: 4px;
  height: 4px;
}

.pupil-eyes {
  position: absolute;
  display: flex;
  gap: 24px;
  transition: all 0.1s ease-out;
}

.pupil-only {
  width: 10px;
  height: 10px;
  background-color: #2D2D2D;
  border-radius: 50%;
  transition: transform 0.05s ease-out;
}

.mouth {
  position: absolute;
  width: 56px;
  height: 3px;
  background-color: #2D2D2D;
  border-radius: 9999px;
  transition: all 0.1s ease-out;
}

.mouth.happy {
  height: 8px;
  border-radius: 0 0 28px 28px;
}

.arm {
  position: absolute;
  width: 15px;
  height: 60px;
  background-color: #6C3FF5;
  border-radius: 8px;
  left: -20px;
  top: 50px;
  transform-origin: top center;
}

/* Footer Links */
.footer-links {
  position: relative;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 24px;
  font-size: 13px;
  color: rgba(0,0,0,0.5);
}

.footer-links a {
  color: inherit;
  text-decoration: none;
  transition: color 0.2s;
}

.footer-links a:hover {
  color: #333;
}

/* Background Effects */
.bg-grid {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, rgba(0,0,0,0.05) 1px, transparent 1px);
  background-size: 20px 20px;
  pointer-events: none;
}

/* Right Section */
.right-section {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: #ffffff;
}

.form-container {
  width: 100%;
  max-width: 360px;
}

.form-header {
  text-align: center;
  margin-bottom: 32px;
}

.form-header h1 {
  font-size: 26px;
  font-weight: bold;
  color: #1a1a1a;
  margin-bottom: 8px;
}

.form-header p {
  color: #888;
  font-size: 13px;
}

/* Tab Switcher */
.tab-switcher {
  display: flex;
  background: #f5f5f5;
  border-radius: 8px;
  padding: 4px;
  margin-bottom: 24px;
}

.tab-switcher button {
  flex: 1;
  padding: 10px;
  border: none;
  background: transparent;
  color: #888;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.tab-switcher button.active {
  background: #6366f1;
  color: white;
}

/* Form Styles */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: #333;
}

.form-group input {
  height: 44px;
  width: 100%;
  padding: 0 12px;
  background-color: #f8f8f8;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  color: #333;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-group input::placeholder {
  color: #aaa;
}

.form-group input:focus {
  border-color: #6366f1;
  outline: none;
}

.form-row {
  display: flex;
  gap: 12px;
}

.form-group.half {
  flex: 1;
}

.password-input {
  position: relative;
}

.password-input input {
  padding-right: 40px;
}

.toggle-password {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 0;
  transition: color 0.2s;
}

.toggle-password:hover {
  color: #333;
}

/* Role Selector */
.role-selector {
  display: flex;
  gap: 12px;
}

.role-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: #f8f8f8;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.role-option input {
  display: none;
}

.role-option.selected {
  border-color: #6366f1;
  background: rgba(99, 102, 241, 0.1);
}

.role-icon {
  font-size: 24px;
}

.role-text {
  font-size: 13px;
  color: #333;
}

/* Error Message */
.error-message {
  padding: 10px;
  font-size: 13px;
  color: #f87171;
  background-color: rgba(248, 113, 113, 0.1);
  border: 1px solid rgba(248, 113, 113, 0.3);
  border-radius: 8px;
}

/* Submit Button */
.submit-btn {
  width: 100%;
  height: 44px;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(99, 102, 241, 0.3);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.submit-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: rgba(255,255,255,0.2);
  transition: left 0.3s;
}

.submit-btn:hover::before {
  left: 100%;
}
</style>
