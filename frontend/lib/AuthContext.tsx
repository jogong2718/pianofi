'use client'
import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import type { User } from '@supabase/supabase-js'

interface AuthContextType {
  user: User | null
  loading: boolean
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  signOut: async () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()
  const supabase = createClient()

  useEffect(() => {
    const getUser = async () => {
      try {
        const {
          data: { user },
          error,
        } = await supabase.auth.getUser()

        if (error) {
          // Handle refresh token errors specifically
          if (error.message.includes('refresh_token_not_found') || 
              error.message.includes('Invalid Refresh Token') ||
              error.message.includes('Auth session missing')) {
            console.log('Session expired - refresh token invalid')
            setUser(null)
            // Don't automatically redirect here, let the user stay on current page
          } else {
            console.error('Auth error:', error)
          }
          setUser(null)
        } else {
          setUser(user)
        }
      } catch (error: any) {
        console.error('Failed to get user:', error)
        setUser(null)
      } finally {
        setLoading(false)
      }
    }

    getUser()

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('Auth event:', event)
        
        if (!session && user) {
          console.log('Session lost - likely token expired')
          setUser(null)
          toast.error('Your session has expired. Please log in again.')
          router.push('/login')
        } else if (session?.user) {
          setUser(session.user)
        } else {
          setUser(null)
        }
        
        setLoading(false)
      }
    )

    return () => subscription.unsubscribe()
  }, [supabase.auth])

  const signOut = async () => {
    try {
      const { error } = await supabase.auth.signOut()
      if (error) {
        toast.error("Logout failed: " + error.message)
      } else {
        setUser(null)
        router.push("/")
        toast.success("Logged out successfully")
      }
    } catch (error) {
      toast.error("An unexpected error occurred during logout")
    }
  }

  const value: AuthContextType = {
    user,
    loading,
    signOut,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
