// src/supabaseClient.js
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL
const supabaseKey = process.env.REACT_APP_SUPABASE_ANON_KEY

// Debug: Log configuration status
console.log('[Supabase] Configuration:', {
  url: supabaseUrl ? '✓ Set' : '✗ Missing',
  key: supabaseKey ? '✓ Set' : '✗ Missing'
})

// Validate configuration
const isConfigured = !!(supabaseUrl && supabaseKey)

let supabase

if (isConfigured) {
  try {
    supabase = createClient(supabaseUrl, supabaseKey, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
        storage: window.localStorage,
      }
    })
    console.log('[Supabase] Client created successfully')
  } catch (error) {
    console.error('[Supabase] Error creating client:', error)
    supabase = null
  }
} else {
  console.warn('[Supabase] Not configured - using mock client')
  supabase = null
}

// Mock client for when Supabase is not configured
const mockClient = {
  auth: {
    getSession: async () => ({ data: { session: null }, error: null }),
    signInWithPassword: async () => ({ data: null, error: { message: 'Supabase non configuré' } }),
    signUp: async () => ({ data: null, error: { message: 'Supabase non configuré' } }),
    signOut: async () => ({ error: null }),
    onAuthStateChange: (callback) => {
      // Call with initial null state
      setTimeout(() => callback('INITIAL_SESSION', null), 0)
      return { data: { subscription: { unsubscribe: () => {} } } }
    },
  },
  from: (table) => ({
    select: (columns) => ({
      eq: (col, val) => ({
        single: () => ({ execute: async () => ({ data: null, error: null }) }),
        execute: async () => ({ data: [], error: null }),
      }),
      execute: async () => ({ data: [], error: null }),
    }),
    insert: (data) => ({ execute: async () => ({ data: null, error: null }) }),
    update: (data) => ({
      eq: (col, val) => ({ execute: async () => ({ data: null, error: null }) }),
    }),
    delete: () => ({
      eq: (col, val) => ({ execute: async () => ({ data: null, error: null }) }),
    }),
  }),
}

// Export the real client or mock
const client = supabase || mockClient
const isSupabaseConfigured = isConfigured && !!supabase

export { client as supabase, isSupabaseConfigured }
