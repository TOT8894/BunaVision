import axios from 'axios'
import { env } from '../config/env'

/**
 * The sole HTTP client for backend requests. Feature APIs will add contract
 * validation and user-safe error normalization here before exposing data to UI.
 */
export const apiClient = axios.create({
  baseURL: env.apiBaseUrl,
  timeout: env.requestTimeoutMs,
})
