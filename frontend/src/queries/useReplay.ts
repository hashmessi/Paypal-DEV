import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'

export function useReplay(id?: string) {
  const queryClient = useQueryClient()

  const query = useQuery({
    queryKey: ['replay', id],
    queryFn: async () => {
      if (!id) throw new Error('Missing purchase id for replay')
      return api.getReplay(id)
    },
    enabled: !!id,
  })

  const verifyMutation = useMutation({
    mutationFn: async () => {
      if (!id) throw new Error('Missing purchase id')
      return api.verifyIntegrity(id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['replay', id] })
    },
  })

  return {
    ...query,
    verifyIntegrity: verifyMutation.mutateAsync,
    isVerifying: verifyMutation.isPending,
    verificationResult: verifyMutation.data,
  }
}

