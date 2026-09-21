import { createClient } from '@supabase/supabase-js';
import { env } from './env.js';

// Used only for the Realtime notification subscription; null when not configured.
export const supabase =
  env.supabaseUrl && env.supabaseKey ? createClient(env.supabaseUrl, env.supabaseKey) : null;
