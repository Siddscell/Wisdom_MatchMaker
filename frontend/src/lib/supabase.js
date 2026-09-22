import { createClient } from '@supabase/supabase-js';
import { env } from './env.js';

// Used only for the Realtime notification subscription; null when not configured.
export const supabase =
  env.supabaseUrl && env.supabaseKey ? createClient(env.supabaseUrl, env.supabaseKey) : null;

/** Upload a listing photo into the signed-in user's folder; returns its public URL. */
export async function uploadListingImage(file) {
  const { data } = await supabase.auth.getUser();
  const extension = file.name.split('.').pop().toLowerCase();
  const path = `${data.user.id}/${crypto.randomUUID()}.${extension}`;
  const bucket = supabase.storage.from('listing-images');
  const { error } = await bucket.upload(path, file, { contentType: file.type });
  if (error) throw new Error(`Photo upload failed: ${error.message}`);
  return bucket.getPublicUrl(path).data.publicUrl;
}
