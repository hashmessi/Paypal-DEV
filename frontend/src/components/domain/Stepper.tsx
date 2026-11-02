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
      <ol className="space-y-2.5">
        {steps.map((step) => {
          const isDone = step.id < currentStep
          const isCurrent = step.id === currentStep
          const isClickable = !locked && isDone && onStepSelect !== undefined

          let circleClass = 'border-[var(--color-line)] bg-white text-[var(--color-muted)]'
          let textClass = 'text-[var(--color-muted)] font-normal'

          if (isDone) {
            circleClass = 'bg-[var(--color-ok-soft)] border-[var(--color-ok-line)] text-[var(--color-ok)] shadow-2xs'
            textClass = 'text-[var(--color-ink)] font-medium'
          } else if (isCurrent) {
            circleClass = 'border-[var(--color-accent)] bg-white text-[var(--color-accent)] ring-3 ring-[var(--color-accent-soft)] shadow-2xs font-bold'
            textClass = 'text-[var(--color-accent)] font-bold'
          }

          return (
            <li key={step.id}>
              <button
                type="button"
                disabled={!isClickable}
                onClick={() => isClickable && onStepSelect(step.id)}
                className={`w-full flex items-center gap-3 p-2.5 rounded-xl text-left transition-all duration-150 ${
                  isCurrent ? 'bg-white shadow-xs border border-[var(--color-line)]' : ''
                } ${
                  isClickable ? 'hover:bg-[var(--color-inset)] cursor-pointer' : 'cursor-default'
                }`}
              >
                <span
                  className={`w-7 h-7 rounded-full border flex items-center justify-center text-[12px] font-semibold shrink-0 transition-colors ${circleClass}`}
                >
                  {isDone ? <Check className="w-3.5 h-3.5 stroke-[2.5]" aria-hidden="true" /> : step.id}
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
