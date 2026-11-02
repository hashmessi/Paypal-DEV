import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'

export function useProof() {
  return useQuery({
    queryKey: ['proof'],
    queryFn: async () => {
      return api.getProof()
    },
  })
}

