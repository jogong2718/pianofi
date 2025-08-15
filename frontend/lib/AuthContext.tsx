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
    const getSession = async () => {
      try {
        const {
          data: { session },
          error,
        } = await supabase.auth.getSession()

        if (error) {
          console.log('Session error:', error.message)
          setUser(null)
        } else if (session?.user) {
          setUser(session.user)
        } else {
          console.log('No active session found')
          setUser(null)
        }
      } catch (error: any) {
        console.log('Failed to get session:', error.message)
        setUser(null)
      } finally {
        setLoading(false)
      }
    }

    getSession()

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('Auth event:', event)
        
        if (event === 'SIGNED_OUT' || !session) {
          setUser(null)
          if (event === 'TOKEN_REFRESHED' && !session) {
            toast.error('Your session has expired. Please log in again.')
            router.push('/login')
          }
        } else if (session?.user) {
          setUser(session.user)
        }
        
        setLoading(false)
      }
    )

    return () => subscription.unsubscribe()
  }, [supabase.auth, router])

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
