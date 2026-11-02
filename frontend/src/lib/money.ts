/**
 * Format integer minor units (e.g. cents) to currency string.
 * Floats are strictly prohibited per UI-SPEC.
 */
export function formatMinor(minorCents: number, currency = 'USD'): string {
  if (!Number.isInteger(minorCents)) {
    // Round to nearest integer if small precision artifact, but enforce integer semantics
    minorCents = Math.round(minorCents)
  }

  const major = minorCents / 100

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(major)
}

export function parseToMinorCents(dollars: string | number): number {
  if (typeof dollars === 'number') {
    return Math.round(dollars * 100)
  }
  const clean = dollars.replace(/[^0-9.]/g, '')
  const val = parseFloat(clean)
  return isNaN(val) ? 0 : Math.round(val * 100)
}

