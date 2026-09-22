// The only place that reads Vite env vars.
export const env = {
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  supabaseUrl: import.meta.env.VITE_SUPABASE_URL || '',
  // Supabase now calls this the "publishable" key; either name works.
  supabaseKey:
    import.meta.env.VITE_SUPABASE_ANON_KEY || import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || '',
};
