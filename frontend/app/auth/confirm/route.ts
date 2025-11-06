import { type EmailOtpType } from '@supabase/supabase-js'
import { type NextRequest } from 'next/server'

import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const token_hash = searchParams.get('token_hash')
  const type = searchParams.get('type') as EmailOtpType | null
  const next = searchParams.get('next') ?? '/dashboard'

  console.log('=== EMAIL CONFIRMATION ===')
  console.log('token_hash:', token_hash)
  console.log('type:', type)
  console.log('next:', next)

  if (token_hash && type) {
    const supabase = await createClient()

    // Handle password recovery
    if (type === 'recovery') {
      const { error } = await supabase.auth.verifyOtp({
        type,
        token_hash,
      })
      if (!error) {
        console.log('Password reset token verified, redirecting to reset password page')
        // After verification, user has a session, so we can redirect to reset-password
        const nextUrl = searchParams.get('next') || '/reset-password'
        redirect(nextUrl)
      } else {
        console.error('Error verifying recovery token:', error)
        redirect(`/error?message=${encodeURIComponent('Failed to verify reset token: ' + error.message)}`)
      }
      return
    }

    const { error } = await supabase.auth.verifyOtp({
      type,
      token_hash,
    })
    if (!error) {
      console.log('Email verified successfully, redirecting to:', next)
      // Add a success parameter to track the redirect
      redirect(`${next}?confirmed=true`)
    } else {
      console.error('Error verifying OTP:', error)
      redirect(`/error?message=${encodeURIComponent('Failed to verify email: ' + error.message)}`)
    }
  }

  // redirect the user to an error page with some instructions
  console.log('Missing token_hash')
  redirect('/error?message=Invalid confirmation link')
}