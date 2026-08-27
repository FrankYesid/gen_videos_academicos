import { get } from './api';

export interface Scene {
  id: number;
  title: string;
  duration_seconds: number;
  narration: string;
  visual_instruction: string;
  on_screen_text: string;
  educational_purpose: string;
}

export interface Script {
  title: string;
  scenes: Scene[];
  total_duration_seconds: number;
}

export interface Video {
  id: string;
  provider: string;
  provider_video_id?: string;
  status: string;
  video_url?: string;
  thumbnail_url?: string;
  duration?: number;
  created_at: string;
  completed_at?: string;
}

export async function getCourseScript(courseId: string) {
  return get<Script>(`/courses/${courseId}/script`);
}

export async function getCourseVideo(courseId: string) {
  return get<Video>(`/courses/${courseId}/video`);
}
