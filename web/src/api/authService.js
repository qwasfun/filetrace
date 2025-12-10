import apiV1 from './apiV1'

export function register(formData) {
  return apiV1.post('/auth/register', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })
}

export function login(formData) {
  return apiV1.post('/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })
}
