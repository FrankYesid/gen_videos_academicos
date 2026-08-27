import { useQuery } from '@tanstack/react-query';
import { listDocuments } from '../services/documents';

export function useDocuments() {
  return useQuery({
    queryKey: ['documents'],
    queryFn: () => listDocuments({ skip: 0, limit: 50 }),
    staleTime: 30_000,
  });
}

