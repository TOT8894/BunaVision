export interface UserOut {
  user_id: string
  email: string
  role: 'user' | 'admin'
  created_at: string
}

export interface TokenOut {
  access_token: string
  token_type: 'bearer'
  expires_in_s: number
}
