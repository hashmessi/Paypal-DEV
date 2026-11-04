import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import type { PurchasePromise } from '../types/api'

export function useReceipt(id?: string) {
  const queryClient = useQueryClient()

  const query = useQuery({
    queryKey: ['receipt', id],
    queryFn: async () => {
      if (!id) throw new Error('Missing receipt id')
      return api.getReceipt(id)
    },
    enabled: !!id,
    refetchInterval: (query) => {
      const p = query.state.data as PurchasePromise | undefined
      if (!p) return false
      // Poll every 3s only while in transient payment state
      const state = p.payment.state
      if (state === 'capturing' || state === 'capture_pending') {
        return 3000
      }
      return false
    },
    refetchIntervalInBackground: false,
  })

  const scenarioMutation = useMutation({
    mutationFn: async ({
      scenarioKey,
    }: {
      scenarioKey:
        | 'refurbished'
        | 'wrong_color'
        | 'corrected'
        | 'label_only'
        | 'late_eta'
        | 'duplicate_event'
        | 'price_change'
        | 'advance_clock'
        | 'prompt_injection'
    }) => {
      if (!id) throw new Error('Missing receipt id')
      return api.sendScenario(id, scenarioKey)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['receipt', id] })
      queryClient.invalidateQueries({ queryKey: ['tower'] })
      queryClient.invalidateQueries({ queryKey: ['replay', id] })
      queryClient.invalidateQueries({ queryKey: ['events'] })
    },
  })

  const voidMutation = useMutation({
    mutationFn: async ({ reason }: { reason: string }) => {
      if (!id) throw new Error('Missing receipt id')
      return api.voidAuthorization(id, reason)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['receipt', id] })
      queryClient.invalidateQueries({ queryKey: ['tower'] })
      queryClient.invalidateQueries({ queryKey: ['replay', id] })
    },
  })

  const reconcileMutation = useMutation({
    mutationFn: async () => {
      if (!id) throw new Error('Missing receipt id')
      return api.reconcile(id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['receipt', id] })
      queryClient.invalidateQueries({ queryKey: ['tower'] })
    },
  })

  return {
    ...query,
    sendScenario: scenarioMutation.mutateAsync,
    isScenarioSending: scenarioMutation.isPending,
    voidAuthorization: voidMutation.mutateAsync,
    isVoiding: voidMutation.isPending,
    reconcile: reconcileMutation.mutateAsync,
    isReconciling: reconcileMutation.isPending,
  }
}

