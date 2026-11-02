import React from 'react'

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string
}

export const Skeleton: React.FC<SkeletonProps> = ({ className = '', ...props }) => {
  return (
    <div
      className={`bg-[var(--color-line)] rounded-[var(--radius-control)] animate-pulse ${className}`}
      aria-hidden="true"
      {...props}
    />
  )
}

