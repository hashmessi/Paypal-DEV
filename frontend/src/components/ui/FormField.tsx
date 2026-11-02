import React from 'react'

export interface FormFieldProps {
  label: string
  hint?: string
  error?: string
  id: string
  required?: boolean
  children: React.ReactNode
}

export const FormField: React.FC<FormFieldProps> = ({
  label,
  hint,
  error,
  id,
  required,
  children,
}) => {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <label
          htmlFor={id}
          className="text-[12px] font-semibold uppercase tracking-[0.04em] text-[var(--color-ink)]"
        >
          {label} {required && <span className="text-[var(--color-bad)]">*</span>}
        </label>
        {hint && <span className="text-[12px] text-[var(--color-muted)]">{hint}</span>}
      </div>
      <div>{children}</div>
      {error && (
        <p id={`${id}-error`} className="text-[12px] text-[var(--color-bad)] font-semibold" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}

