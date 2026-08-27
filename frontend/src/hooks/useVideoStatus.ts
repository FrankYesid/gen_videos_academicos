import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getCourseStatus } from '../services/courses';

export function useVideoStatus(courseId?: string, enabled = true) {
  const query = useQuery({
    queryKey: ['course-status', courseId],
    queryFn: () => getCourseStatus(courseId!),
    enabled: Boolean(courseId) && enabled,
    refetchInterval: (q) => {
      const data = q.state.data;
      if (!data) return 5000;
      if (['COMPLETED', 'FAILED'].includes(data.status)) return false;
      return 3000;
    },
  });

  useEffect(() => {
    return () => void 0;
  }, [courseId]);

  return query;
}
