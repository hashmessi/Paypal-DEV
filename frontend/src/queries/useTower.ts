import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'

export function useTower() {
  const queryClient = useQueryClient()

  const query = useQuery({
    queryKey: ['tower'],
    queryFn: async () => {
      return api.getTower()
    },
    refetchInterval: 10000,
    refetchIntervalInBackground: false,
  })

  const runScenarioMutation = useMutation({
    mutationFn: async (instruction?: string) => {
      return api.runDemoScenario(instruction)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tower'] })
      queryClient.invalidateQueries({ queryKey: ['events'] })
    },
  })

  const voidMutation = useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason: string }) => {
      return api.voidAuthorization(id, reason)
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['tower'] })
      queryClient.invalidateQueries({ queryKey: ['receipt', id] })
    },
  })

  const reconcileMutation = useMutation({
    mutationFn: async (id: string) => {
      return api.reconcile(id)
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['tower'] })
      queryClient.invalidateQueries({ queryKey: ['receipt', id] })
    },
  })

  return {
    ...query,
    runDemoScenario: runScenarioMutation.mutateAsync,
    isRunningDemo: runScenarioMutation.isPending,
    voidAuthorization: voidMutation.mutateAsync,
    isVoiding: voidMutation.isPending,
    reconcile: reconcileMutation.mutateAsync,
    isReconciling: reconcileMutation.isPending,
  }
}

