import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client.js';
import { supabase } from '../lib/supabase.js';

// Matching runs in the background after a submit, so match lists refresh on their own.
const LIVE_REFRESH_MS = 10_000;
const POLL_FALLBACK_MS = 15_000;

export const useMeta = () =>
  useQuery({ queryKey: ['meta'], queryFn: api.meta, staleTime: Infinity });

export const useSummary = () =>
  useQuery({ queryKey: ['summary'], queryFn: api.summary, refetchInterval: LIVE_REFRESH_MS });

/** Public listings. @param {'requirements'|'offerings'} table */
export const useListings = (table, params) =>
  useQuery({ queryKey: [table, params], queryFn: () => api[table].list(params) });

/** The logged-in owner's own listings (full detail). */
export const useMyListings = (table) =>
  useQuery({ queryKey: [table, 'mine'], queryFn: api[table].mine });

export const useMatches = (params) =>
  useQuery({
    queryKey: ['matches', params],
    queryFn: () => api.matches(params),
    refetchInterval: LIVE_REFRESH_MS,
  });

export const useOutbox = () => useQuery({ queryKey: ['outbox'], queryFn: api.outbox });

export function useSetMatchStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }) => api.setMatchStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['matches'] });
      queryClient.invalidateQueries({ queryKey: ['summary'] });
    },
  });
}

export function useMarkRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.markRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  });
}

/**
 * The logged-in user's notifications (`email` keys the cache and the Realtime filter). Supabase Realtime pushes inserts when configured;
 * otherwise (or if the subscription fails) the query polls every 15 seconds.
 */
export function useMyNotifications(email) {
  const queryClient = useQueryClient();
  const [live, setLive] = useState(false);

  useEffect(() => {
    if (!supabase || !email) return undefined;
    const channel = supabase
      .channel(`notifications:${email}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'notifications',
          filter: `recipient_email=eq.${email}`,
        },
        () => {
          for (const key of ['notifications', 'matches', 'summary']) {
            queryClient.invalidateQueries({ queryKey: [key] });
          }
        },
      )
      .subscribe((status) => setLive(status === 'SUBSCRIBED'));
    return () => {
      setLive(false);
      supabase.removeChannel(channel);
    };
  }, [email, queryClient]);

  return useQuery({
    queryKey: ['notifications', email],
    queryFn: () => api.notifications(),
    enabled: Boolean(email),
    refetchInterval: live ? false : POLL_FALLBACK_MS,
    refetchIntervalInBackground: true, // keep the bell current while the tab is hidden
  });
}
