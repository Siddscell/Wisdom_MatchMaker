import { useState } from 'react';
import { Link, Navigate, useNavigate, useOutletContext, useSearchParams } from 'react-router-dom';
import { supabase } from '../lib/supabase.js';

const ROLES = [
  ['client', 'I need products', 'Post requirements, get ranked suppliers.'],
  ['supplier', 'I supply products', 'List offerings, hear about matching buyers.'],
];

/** Log in or register (mode), via Supabase Auth: email + password. */
export default function AuthPage({ mode }) {
  const { account } = useOutletContext();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [role, setRole] = useState(params.get('role') === 'supplier' ? 'supplier' : 'client');
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  const [checkEmail, setCheckEmail] = useState(false);
  const registering = mode === 'register';

  if (account) return <Navigate to="/me" replace />;
  if (!supabase) {
    return (
      <p role="alert" className="text-danger">
        Accounts need VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in frontend/.env.
      </p>
    );
  }

  const submit = async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const email = String(form.get('email')).trim();
    const password = String(form.get('password'));
    setPending(true);
    setError('');
    const { data, error: failure } = registering
      ? await supabase.auth.signUp({
          email,
          password,
          options: { data: { role, company: String(form.get('company')).trim() } },
        })
      : await supabase.auth.signInWithPassword({ email, password });
    setPending(false);
    if (failure) return setError(failure.message);
    if (data.session) return navigate('/me');
    setCheckEmail(true); // email confirmation is switched on in Supabase
  };

  if (checkEmail) {
    return (
      <div role="status" className="card mx-auto max-w-md">
        <h1 className="text-2xl font-semibold">Check your email</h1>
        <p className="mt-2 text-muted">
          We sent a confirmation link. After confirming,{' '}
          <Link to="/login" className="text-accent underline underline-offset-2">
            log in
          </Link>
          .
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md">
      <h1 className="text-3xl font-semibold">{registering ? 'Create your account' : 'Log in'}</h1>
      <form onSubmit={submit} className="card mt-6 space-y-5">
        {registering && (
          <fieldset>
            <legend className="label">I am a</legend>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {ROLES.map(([value, title, text]) => (
                <label
                  key={value}
                  className={`cursor-pointer rounded-md border p-3 text-sm ${role === value ? 'border-accent bg-accent-soft' : 'border-line'}`}
                >
                  <input
                    type="radio"
                    name="role"
                    value={value}
                    checked={role === value}
                    onChange={() => setRole(value)}
                    className="sr-only"
                  />
                  <span className="font-medium">{title}</span>
                  <span className="mt-1 block text-xs text-muted">{text}</span>
                </label>
              ))}
            </div>
          </fieldset>
        )}
        {registering && (
          <div>
            <label htmlFor="company" className="label">
              Company name
            </label>
            <input id="company" name="company" required minLength={2} className="input mt-1.5" />
          </div>
        )}
        <div>
          <label htmlFor="email" className="label">
            Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            required
            autoComplete="email"
            className="input mt-1.5"
          />
        </div>
        <div>
          <label htmlFor="password" className="label">
            Password
          </label>
          <input
            id="password"
            name="password"
            type="password"
            required
            minLength={registering ? 8 : undefined}
            autoComplete={registering ? 'new-password' : 'current-password'}
            className="input mt-1.5"
          />
          {registering && <p className="mt-1 text-xs text-muted">At least 8 characters.</p>}
        </div>
        {error && (
          <p role="alert" className="text-sm font-medium text-danger">
            {error}
          </p>
        )}
        <button type="submit" className="btn-primary w-full" disabled={pending}>
          {pending ? 'Please wait…' : registering ? 'Create account' : 'Log in'}
        </button>
        <p className="text-center text-sm text-muted">
          {registering ? 'Already registered? ' : 'New here? '}
          <Link
            to={registering ? '/login' : '/register'}
            className="text-accent underline underline-offset-2"
          >
            {registering ? 'Log in' : 'Create an account'}
          </Link>
        </p>
      </form>
    </div>
  );
}
