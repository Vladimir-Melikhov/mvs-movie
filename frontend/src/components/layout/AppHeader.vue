<template>
  <nav
    class="fixed top-0 w-full z-50 transition-all duration-700"
    :class="headerClasses"
    :style="headerStyle"
  >
    <div class="max-w-7xl mx-auto px-6 py-5">
      <div class="flex items-center justify-between">
        <!-- Logo -->
        <div
          class="text-xl font-light tracking-[0.3em] transition-colors duration-700"
          :class="textColorClass"
        >
          <router-link to="/" class="hover:opacity-60 transition-opacity duration-500">
            MVS
          </router-link>
        </div>

        <!-- Center Navigation -->
        <div
          class="hidden md:flex items-center space-x-12 text-xs font-light tracking-[0.25em] transition-colors duration-700"
          :class="textColorClass"
        >
          <router-link to="/products" class="nav-link opacity-70 hover:opacity-100 transition-all duration-500">
            COLLECTION
          </router-link>
          <router-link to="/products?gender=men" class="nav-link opacity-70 hover:opacity-100 transition-all duration-500">
            MEN
          </router-link>
          <router-link to="/products?gender=women" class="nav-link opacity-70 hover:opacity-100 transition-all duration-500">
            WOMEN
          </router-link>
        </div>

        <!-- Right Navigation -->
        <div
          class="hidden md:flex items-center space-x-8 text-xs tracking-[0.2em] transition-colors duration-700"
          :class="textColorClass"
        >
          <router-link v-if="!isAuthenticated" to="/login" class="nav-link opacity-70 hover:opacity-100 transition-all duration-500">
            LOG IN
          </router-link>
          <router-link v-if="isAuthenticated" to="/profile" class="nav-link opacity-70 hover:opacity-100 transition-all duration-500">
            PROFILE
          </router-link>
        </div>

        <!-- Mobile Menu Button -->
        <button
          @click="mobileMenuOpen = !mobileMenuOpen"
          class="md:hidden transition-colors duration-700"
          :class="textColorClass"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M4 6h16M4 12h16M4 18h16"></path>
          </svg>
        </button>
      </div>
    </div>

    <!-- Mobile Menu -->
    <div
      v-show="mobileMenuOpen"
      class="md:hidden border-t transition-all duration-700"
      :class="mobileMenuClasses"
    >
      <div class="px-6 py-6 space-y-6 text-xs tracking-[0.2em]">
        <router-link to="/products" class="block opacity-70 hover:opacity-100 transition-opacity" @click="mobileMenuOpen = false">
          COLLECTION
        </router-link>
        <router-link to="/products?gender=men" class="block opacity-70 hover:opacity-100 transition-opacity" @click="mobileMenuOpen = false">
          MEN
        </router-link>
        <router-link to="/products?gender=women" class="block opacity-70 hover:opacity-100 transition-opacity" @click="mobileMenuOpen = false">
          WOMEN
        </router-link>
        <div
          class="pt-6 border-t transition-colors duration-700"
          :class="mobileBorderClass"
        >
          <router-link
            v-if="!isAuthenticated"
            to="/login"
            class="block opacity-70 hover:opacity-100 transition-opacity"
            @click="mobileMenuOpen = false"
          >
            LOG IN
          </router-link>
          <router-link
            v-if="isAuthenticated"
            to="/profile"
            class="block opacity-70 hover:opacity-100 transition-opacity"
            @click="mobileMenuOpen = false"
          >
            PROFILE
          </router-link>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  variant: {
    type: String,
    default: 'light',
    validator: (value) => ['light', 'dark'].includes(value)
  }
})

const authStore = useAuthStore()
const scrolled = ref(false)
const mobileMenuOpen = ref(false)

const isAuthenticated = computed(() => authStore.isAuthenticated)

// УПРОЩЕНО: Вычисляемые свойства для классов
const isDark = computed(() => props.variant === 'dark' || scrolled.value)

const headerClasses = computed(() =>
  isDark.value ? 'bg-black/90 border-white/10' : 'bg-white/90 border-gray-200'
)

const headerStyle = computed(() => ({
  borderBottomWidth: '1px',
  borderBottomStyle: 'solid'
}))

const textColorClass = computed(() =>
  isDark.value ? 'text-white' : 'text-black'
)

const mobileMenuClasses = computed(() =>
  isDark.value
    ? 'bg-black/95 border-white/10 text-white'
    : 'bg-white border-gray-200 text-black'
)

const mobileBorderClass = computed(() =>
  isDark.value ? 'border-white/10' : 'border-gray-200'
)

const handleScroll = () => {
  scrolled.value = window.scrollY > 100
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
  handleScroll()
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.nav-link {
  position: relative;
}

.nav-link::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 0;
  height: 1px;
  background: currentColor;
  transition: width 0.5s ease;
}

.nav-link:hover::after {
  width: 100%;
}
</style>
