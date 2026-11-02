import React from 'react'
import { Check } from 'lucide-react'

export interface StepItem {
  id: number
  title: string
}

export interface StepperProps {
  steps: StepItem[]
  currentStep: number
  onStepSelect?: (step: number) => void
  locked?: boolean
}

export const Stepper: React.FC<StepperProps> = ({
  steps,
  currentStep,
  onStepSelect,
  locked = false,
}) => {
  return (
    <nav aria-label="Purchase progress" className="w-full md:w-60 shrink-0">
      <ol className="space-y-3">
        {steps.map((step) => {
          const isDone = step.id < currentStep
          const isCurrent = step.id === currentStep
          const isClickable = !locked && isDone && onStepSelect !== undefined

          let circleClass = 'border-[var(--color-line)] bg-white text-[var(--color-muted)]'
          let textClass = 'text-[var(--color-muted)] font-normal'

          if (isDone) {
            circleClass = 'bg-[var(--color-ok-soft)] border-[var(--color-ok-line)] text-[var(--color-ok)]'
            textClass = 'text-[var(--color-ink)] font-normal'
          } else if (isCurrent) {
            circleClass = 'border-[var(--color-accent)] bg-white text-[var(--color-accent)] ring-2 ring-[var(--color-accent-soft)]'
            textClass = 'text-[var(--color-ink)] font-semibold'
          }

          return (
            <li key={step.id}>
              <button
                type="button"
                disabled={!isClickable}
                onClick={() => isClickable && onStepSelect(step.id)}
                className={`w-full flex items-center gap-3 p-2.5 rounded-[var(--radius-control)] text-left transition-colors ${
                  isClickable ? 'hover:bg-[var(--color-inset)] cursor-pointer' : 'cursor-default'
                }`}
              >
                <span
                  className={`w-7 h-7 rounded-full border flex items-center justify-center text-[12px] font-semibold shrink-0 transition-colors ${circleClass}`}
                >
                  {isDone ? <Check className="w-4 h-4" aria-hidden="true" /> : step.id}
                </span>
                <span className={`text-[14px] leading-tight ${textClass}`}>{step.title}</span>
              </button>
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
