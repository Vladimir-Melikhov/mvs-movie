<template>
    <div class="min-h-screen bg-white">
      <!-- Navigation -->
      <AppHeader variant="dark" />
  
      <!-- Loading State -->
      <div v-if="productsStore.loading" class="flex items-center justify-center py-20 mt-20">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
  
      <!-- Error State -->
      <div
        v-else-if="productsStore.error"
        class="max-w-7xl mx-auto px-6 py-20 text-center mt-20"
      >
        <h2 class="text-2xl font-light text-gray-900 mb-4">Product Not Found</h2>
        <p class="text-gray-600 mb-8">The product you're looking for doesn't exist.</p>
        <router-link
          to="/products"
          class="inline-block px-8 py-3 border border-black text-sm font-medium tracking-widest text-black bg-white hover:bg-black hover:text-white transition-all"
        >
          BACK TO PRODUCTS
        </router-link>
      </div>
  
      <!-- Product Detail -->
      <div class="mt-20">
        <ProductDetail v-if="productsStore.currentProduct" :product="productsStore.currentProduct" />
      </div>
  
      <!-- Related Products -->
      <div
        v-if="productsStore.relatedProducts.length > 0"
        class="bg-gray-50 border-t border-gray-200 py-16"
      >
        <div class="max-w-7xl mx-auto px-6">
          <h2 class="text-2xl font-light text-gray-900 mb-8 tracking-wide">
            You May Also Like
          </h2>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <ProductCard
              v-for="product in productsStore.relatedProducts"
              :key="product.id"
              :product="product"
            />
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { onMounted } from 'vue'
  import { useRoute } from 'vue-router'
  import { useProductsStore } from '@/stores/products'
  import ProductDetail from '@/components/product/ProductDetail.vue'
  import ProductCard from '@/components/product/ProductCard.vue'
  import AppHeader from '@/components/layout/AppHeader.vue'
  
  const route = useRoute()
  const productsStore = useProductsStore()
  
  onMounted(async () => {
    const slug = route.params.slug
    await productsStore.fetchProductBySlug(slug)
  
    if (productsStore.currentProduct) {
      await productsStore.fetchRelatedProducts(slug)
    }
  })
  </script>