import React from 'react'

export interface Column<T> {
  header: string
  accessor?: keyof T | ((row: T) => React.ReactNode)
  className?: string
  width?: string
}

export interface DataTableProps<T> {
  columns: Column<T>[]
  data: T[]
  keyExtractor: (row: T) => string
  onRowClick?: (row: T) => void
  emptyState?: React.ReactNode
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  onRowClick,
  emptyState,
}: DataTableProps<T>) {
  if (data.length === 0 && emptyState) {
    return <>{emptyState}</>
  }

  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full min-w-[880px] text-left border-collapse">
        <thead>
          <tr className="bg-[var(--color-inset)] border-b border-[var(--color-line)]">
            {columns.map((col, idx) => (
              <th
                key={idx}
                className={`py-3 px-4 text-[12px] font-semibold uppercase tracking-[0.04em] text-[var(--color-muted)] select-none ${
                  col.className || ''
                }`}
                style={col.width ? { width: col.width } : undefined}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-[var(--color-line)] bg-white text-[14px]">
          {data.map((row) => (
            <tr
              key={keyExtractor(row)}
              onClick={() => onRowClick?.(row)}
              tabIndex={onRowClick ? 0 : undefined}
              onKeyDown={
                onRowClick
                  ? (e) => {
                      if (e.target === e.currentTarget && (e.key === 'Enter' || e.key === ' ')) {
                        e.preventDefault()
                        onRowClick(row)
                      }
                    }
                  : undefined
              }
              className={`h-14 transition-colors ${
                onRowClick ? 'cursor-pointer hover:bg-[var(--color-inset)]' : ''
              }`}
            >
              {columns.map((col, cIdx) => {
                let content: React.ReactNode = null
                if (typeof col.accessor === 'function') {
                  content = col.accessor(row)
                } else if (col.accessor) {
                  content = row[col.accessor] as React.ReactNode
                }

                return (
                  <td key={cIdx} className={`py-3 px-4 ${col.className || ''}`}>
                    {content}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

