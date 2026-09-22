import { useId } from 'react';
import { useForm } from 'react-hook-form';
import { ApiError } from '../api/client.js';
import { zodResolver } from '../lib/schemas.js';

/**
 * @typedef {{ name: string, label: string, type?: 'text'|'email'|'number'|'textarea'|'select',
 *   options?: string[], hint?: string, wide?: boolean, optional?: boolean,
 *   suggest?: (value: string) => Promise<Record<string, string|null>> }} FieldSpec
 *   suggest: on blur, fills still-empty fields from the returned values.
 */

function Control({ field, id, register, invalid, describedBy }) {
  const common = {
    id,
    className: 'input',
    'aria-invalid': invalid,
    'aria-describedby': describedBy,
    ...register(field.name),
  };
  if (field.type === 'textarea') return <textarea rows={3} {...common} />;
  if (field.type === 'select') {
    return (
      <select {...common}>
        <option value="">Choose…</option>
        {field.options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    );
  }
  if (field.type === 'number')
    return <input type="number" step="any" inputMode="decimal" {...common} />;
  return <input type={field.type ?? 'text'} autoComplete="off" {...common} />;
}

/** One form component for both portals: fields come from a spec list, rules from a zod schema. */
export default function EntityForm({ fields, schema, defaultValues, submitLabel, onSubmit }) {
  const formId = useId();
  const {
    register: baseRegister,
    handleSubmit,
    setError,
    getValues,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm({ resolver: zodResolver(schema), defaultValues });

  const register = (name) => {
    const spec = fields.find((f) => f.name === name);
    if (!spec?.suggest) return baseRegister(name);
    const onBlur = async (event) => {
      if (event.target.value.trim().length < 2) return;
      const suggested = await spec.suggest(event.target.value).catch(() => ({}));
      for (const [key, value] of Object.entries(suggested)) {
        if (value && !getValues(key)) setValue(key, value, { shouldValidate: true });
      }
    };
    return baseRegister(name, { onBlur });
  };

  const submit = handleSubmit(async (values) => {
    try {
      await onSubmit(values);
    } catch (error) {
      const fields = error instanceof ApiError ? error.fields : {};
      for (const [name, message] of Object.entries(fields)) setError(name, { message });
      setError('root', { message: error.message });
    }
  });

  return (
    <form onSubmit={submit} noValidate className="grid gap-x-4 gap-y-5 sm:grid-cols-2">
      {fields.map((field) => {
        const id = `${formId}-${field.name}`;
        const error = errors[field.name]?.message;
        const describedBy = [field.hint && `${id}-hint`, error && `${id}-error`]
          .filter(Boolean)
          .join(' ');
        return (
          <div key={field.name} className={field.wide ? 'sm:col-span-2' : undefined}>
            <label htmlFor={id} className="label">
              {field.label}
              {field.optional && <span className="font-normal text-muted"> (optional)</span>}
            </label>
            <div className="mt-1.5">
              <Control
                field={field}
                id={id}
                register={register}
                invalid={Boolean(error)}
                describedBy={describedBy || undefined}
              />
            </div>
            {field.hint && (
              <p id={`${id}-hint`} className="mt-1 text-xs text-muted">
                {field.hint}
              </p>
            )}
            {error && (
              <p id={`${id}-error`} className="mt-1 text-xs font-medium text-danger">
                {error}
              </p>
            )}
          </div>
        );
      })}
      <div className="flex flex-wrap items-center gap-4 sm:col-span-2">
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Submitting…' : submitLabel}
        </button>
        {errors.root && (
          <p role="alert" className="text-sm font-medium text-danger">
            {errors.root.message}
          </p>
        )}
      </div>
    </form>
  );
}
