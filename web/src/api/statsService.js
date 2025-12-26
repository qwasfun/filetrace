import service from '@/utils/service'

export default {
  getStats() {
    return service.get('/v1/stats/')
  },
}
