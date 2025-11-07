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

    const { error } = await supabase.auth.verifyOtp({
      type,
      token_hash,
    })
    if (!error) {
      console.log('✅ Email verified successfully, redirecting to:', next)
      // Add a success parameter to track the redirect
      redirect(`${next}?confirmed=true`)
    } else {
      console.error('❌ Error verifying OTP:', error)
      redirect(`/error?message=${encodeURIComponent('Failed to verify email: ' + error.message)}`)
    }
  }

  // redirect the user to an error page with some instructions
  console.log('❌ Missing token_hash or type')
  redirect('/error?message=Invalid confirmation link')
}