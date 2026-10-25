import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type PropsWithChildren,
} from 'react'
import type { UserOut } from '../types/auth'
import { loginUser, registerUser, fetchCurrentUser } from '../services/authService'

interface AuthContextValue {
  authToken: string | null
  currentUser: UserOut | null
  authLoading: boolean

  handleLogin: (email: string, password: string) => Promise<void>
  handleRegister: (email: string, password: string) => Promise<void>
  handleLogout: () => void

  loginError: string | null
  loginLoading: boolean
  registerError: string | null
  registerLoading: boolean

  clearLoginError: () => void
  clearRegisterError: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: PropsWithChildren) {
  const [authToken, setAuthToken] = useState<string | null>(() =>
    localStorage.getItem('bv_token'),
  )
  const [currentUser, setCurrentUser] = useState<UserOut | null>(null)
  const [authLoading, setAuthLoading] = useState<boolean>(!!localStorage.getItem('bv_token'))

  const [loginError, setLoginError] = useState<string | null>(null)
  const [loginLoading, setLoginLoading] = useState(false)
  const [registerError, setRegisterError] = useState<string | null>(null)
  const [registerLoading, setRegisterLoading] = useState(false)

  // Validate stored token on mount
  useEffect(() => {
    const token = localStorage.getItem('bv_token')
    if (!token) {
      setAuthLoading(false)
      return
    }
    fetchCurrentUser(token)
      .then((user) => {
        setCurrentUser(user)
        setAuthToken(token)
      })
      .catch(() => {
        localStorage.removeItem('bv_token')
        setAuthToken(null)
        setCurrentUser(null)
      })
      .finally(() => setAuthLoading(false))
  }, [])

  const handleLogin = useCallback(async (email: string, password: string) => {
    setLoginLoading(true)
    setLoginError(null)
    try {
      const tokenData = await loginUser(email, password)
      const token = tokenData.access_token
      localStorage.setItem('bv_token', token)
      setAuthToken(token)
      const user = await fetchCurrentUser(token)
      setCurrentUser(user)
    } catch {
      setLoginError('Invalid email or password. Please try again.')
      throw new Error('Login failed')
    } finally {
      setLoginLoading(false)
    }
  }, [])

  const handleRegister = useCallback(async (email: string, password: string) => {
    setRegisterLoading(true)
    setRegisterError(null)
    try {
      await registerUser(email, password)
      // Auto-login after registration
      const tokenData = await loginUser(email, password)
      const token = tokenData.access_token
      localStorage.setItem('bv_token', token)
      setAuthToken(token)
      const user = await fetchCurrentUser(token)
      setCurrentUser(user)
    } catch (err: unknown) {
      const msg =
        err instanceof Error && err.message.includes('409')
          ? 'An account with this email already exists.'
          : 'Registration failed. Please try again.'
      setRegisterError(msg)
      throw new Error('Register failed')
    } finally {
      setRegisterLoading(false)
    }
  }, [])

  const handleLogout = useCallback(() => {
    localStorage.removeItem('bv_token')
    setAuthToken(null)
    setCurrentUser(null)
  }, [])

  const clearLoginError = useCallback(() => setLoginError(null), [])
  const clearRegisterError = useCallback(() => setRegisterError(null), [])

  return (
    <AuthContext
      value={{
        authToken,
        currentUser,
        authLoading,
        handleLogin,
        handleRegister,
        handleLogout,
        loginError,
        loginLoading,
        registerError,
        registerLoading,
        clearLoginError,
        clearRegisterError,
      }}
    >
      {children}
    </AuthContext>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
