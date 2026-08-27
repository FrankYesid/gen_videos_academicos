import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  approveScript,
  generateScript,
  generateVideo,
  getCourse,
  regenerateScript,
  analyzeCourse,
} from '../services/courses';

export function useCourse(id?: string) {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ['course', id],
    queryFn: () => (id ? getCourse(id) : Promise.reject(new Error('no id'))),
    enabled: Boolean(id),
  });

  const analyze = useMutation({
    mutationFn: analyzeCourse,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['course', id] }),
  });

  const script = useMutation({
    mutationFn: generateScript,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['course', id] }),
  });

  const approve = useMutation({
    mutationFn: approveScript,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['course', id] }),
  });

  const regenerate = useMutation({
    mutationFn: regenerateScript,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['course', id] }),
  });

  const video = useMutation({
    mutationFn: generateVideo,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['course', id] }),
  });

  return { query, analyze, script, approve, regenerate, video };
}
