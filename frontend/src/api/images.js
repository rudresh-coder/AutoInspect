import axios from 'axios'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
})

export async function uploadImage(file) {
  const formData = new FormData()
  formData.append('image', file)

  const response = await api.post('/api/v1/images', formData)

  return response.data
}

export async function getImageStatus(processingId) {
  const response = await api.get(
    `/api/v1/images/${processingId}`
  )

  return response.data
}