import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { cityApi } from '@/api/modules'

export const useCityStore = defineStore('city', () => {
  const cities = ref([])
  const currentCityId = ref(null)
  const loading = ref(false)

  const currentCity = computed(() =>
    cities.value.find((c) => c.id === currentCityId.value) || null
  )

  const citiesByProvince = computed(() => {
    const map = {}
    for (const city of cities.value) {
      if (!map[city.province]) map[city.province] = []
      map[city.province].push(city)
    }
    return map
  })

  async function fetchCities() {
    loading.value = true
    try {
      cities.value = await cityApi.getList()
    } finally {
      loading.value = false
    }
  }

  function selectCity(cityId) {
    currentCityId.value = cityId
  }

  return {
    cities, currentCityId, loading,
    currentCity, citiesByProvince,
    fetchCities, selectCity,
  }
})
