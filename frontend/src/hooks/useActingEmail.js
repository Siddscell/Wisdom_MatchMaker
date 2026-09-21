import { useCallback, useState } from 'react';

const KEY = 'acting-as-email';

function read() {
  try {
    return localStorage.getItem(KEY) || '';
  } catch {
    return ''; // storage blocked (private mode etc.): identity just is not remembered
  }
}

/** Demo identity: the email the user says they are. No password, by design. */
export function useActingEmail() {
  const [email, setEmailState] = useState(read);
  const setEmail = useCallback((value) => {
    const next = value.trim().toLowerCase();
    setEmailState(next);
    try {
      localStorage.setItem(KEY, next);
    } catch {
      /* not persisted */
    }
  }, []);
  return [email, setEmail];
}
