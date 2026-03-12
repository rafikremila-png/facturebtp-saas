// src/supabaseClient.js
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL
const supabaseKey = process.env.REACT_APP_SUPABASE_ANON_KEY

// Validate configuration
if (!supabaseUrl || !supabaseKey) {
  console.error('Supabase configuration missing!', {
    url: supabaseUrl ? 'OK' : 'MISSING',
    key: supabaseKey ? 'OK' : 'MISSING'
  })
}

// Create client with error handling
let supabase

try {
  if (supabaseUrl && supabaseKey) {
    supabase = createClient(supabaseUrl, supabaseKey, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true
      }
    })
  } else {
    // Create a mock client that will fail gracefully
    console.error('Creating mock Supabase client - auth will not work')
    supabase = {
      auth: {
        getSession: async () => ({ data: { session: null }, error: new Error('Supabase not configured') }),
        signInWithPassword: async () => ({ data: null, error: new Error('Supabase not configured') }),
        signUp: async () => ({ data: null, error: new Error('Supabase not configured') }),
        signOut: async () => ({ error: null }),
        onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } } }),
      },
      from: () => ({
        select: () => ({ eq: () => ({ single: () => ({ execute: async () => ({ data: null, error: new Error('Supabase not configured') }) }) }) }),
        insert: () => ({ execute: async () => ({ data: null, error: new Error('Supabase not configured') }) }),
      }),
    }
  }
} catch (error) {
  console.error('Error creating Supabase client:', error)
  throw error
}

export { supabase }
