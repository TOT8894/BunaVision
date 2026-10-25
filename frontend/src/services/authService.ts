import axios from 'axios'
import { env } from '../config/env'
import type { UserOut, TokenOut } from '../types/auth'

const API_BASE = env.apiBaseUrl

export async function loginUser(email: string, password: string): Promise<TokenOut> {
  const response = await axios.post<TokenOut>(
    `${API_BASE}/auth/login`,
    { email, password },
    { timeout: 10000 }
  )
  return response.data
}

export async function registerUser(email: string, password: string): Promise<UserOut> {
  const response = await axios.post<UserOut>(
    `${API_BASE}/auth/register`,
    { email, password },
    { timeout: 10000 }
  )
  return response.data
}

export async function fetchCurrentUser(token: string): Promise<UserOut> {
  const response = await axios.get<UserOut>(
    `${API_BASE}/auth/me`,
    {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 5000,
    }
  )
  return response.data
}
