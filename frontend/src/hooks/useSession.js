import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase.js';

/** Supabase auth session: undefined while loading, null when logged out. */
export function useSession() {
  const [session, setSession] = useState(supabase ? undefined : null);
  useEffect(() => {
    if (!supabase) return undefined;
    supabase.auth.getSession().then(({ data }) => setSession(data.session));
    const { data } = supabase.auth.onAuthStateChange((_event, next) => setSession(next));
    return () => data.subscription.unsubscribe();
  }, []);
  return session;
}

/** @param {import('@supabase/supabase-js').Session | null | undefined} session */
export const accountOf = (session) =>
  session && {
    email: session.user.email.toLowerCase(),
    role: session.user.user_metadata?.role,
    company: session.user.user_metadata?.company ?? '',
  };
