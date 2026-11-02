import React from 'react'
import { Loader2 } from 'lucide-react'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'danger-solid'
  size?: 'sm' | 'md'
  loading?: boolean
  icon?: React.ReactNode
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'secondary',
      size = 'md',
      loading = false,
      icon,
      disabled,
      children,
      className = '',
      type = 'button',
      ...props
    },
    ref
  ) => {
    const base =
      'inline-flex items-center justify-center font-semibold transition-colors duration-100 disabled:opacity-50 disabled:cursor-not-allowed select-none focus-visible:outline-2 focus-visible:outline-[var(--color-accent)] focus-visible:outline-offset-2'

    const sizeClass =
      size === 'sm'
        ? 'h-8 sm:h-8 max-sm:h-10 px-3 text-[12px] gap-1.5 rounded-[var(--radius-control)]'
        : 'h-10 px-4 text-[14px] gap-2 rounded-[var(--radius-control)]'

    let variantClass = ''
    switch (variant) {
      case 'primary':
        variantClass =
          'bg-[var(--color-accent)] text-white hover:bg-[var(--color-accent-hover)] active:bg-[var(--color-accent-hover)] border border-transparent'
        break
      case 'secondary':
        variantClass =
          'bg-white text-[var(--color-ink)] border border-[var(--color-line-strong)] hover:bg-[var(--color-canvas)] active:bg-[var(--color-inset)]'
        break
      case 'danger':
        variantClass =
          'bg-white text-[var(--color-bad)] border border-[var(--color-bad-line)] hover:bg-[var(--color-bad-soft)]'
        break
      case 'danger-solid':
        variantClass =
          'bg-[var(--color-bad)] text-white border border-transparent hover:bg-[#991b1b] active:bg-[#7f1d1d]'
        break
      case 'ghost':
        variantClass =
          'bg-transparent text-[var(--color-ink)] hover:bg-[var(--color-inset)] border border-transparent'
        break
    }

    return (
      <button
        ref={ref}
        type={type}
        disabled={disabled || loading}
        className={`${base} ${sizeClass} ${variantClass} ${className}`}
        {...props}
      >
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
        ) : (
          icon && <span className="inline-flex shrink-0">{icon}</span>
        )}
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'

