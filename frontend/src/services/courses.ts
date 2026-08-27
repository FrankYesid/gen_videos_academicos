import { get, post } from './api';
import type { Course, CourseListItem } from '../types/course';
import type { Script } from '../types/script';
import type { PedagogicalDesign } from '../types/pedagogical';
import type { QAResult } from '../types/qa';
import type { Analysis } from '../types/analysis';
import type { AxiosError } from 'axios';

export const isNotFoundError = (e: unknown): boolean => {
  const err = e as AxiosError<any> | undefined;
  return !!err && (err?.status === 404 || err?.response?.status === 404);
};

export interface VideoInfo {
  id: string;
  url?: string;
  thumbnail_url?: string;
  duration?: number;
  status?: string;
  provider?: string;
  provider_video_id?: string;
  course_id: string;
}

export interface CreateCourseInput {
  title: string;
  subject: string;
  level?: string;
  language?: string;
  estimated_duration_minutes?: number;
  description?: string;
  document_id?: string;
}

export interface CourseStatus {
  course_id: string;
  status: string;
  progress: number;
  current_step?: string;
  video?: { url: string; thumbnail_url?: string; duration: number };
  qa?: { status: string; score: number };
}

interface ListCoursesResponse {
  items: CourseListItem[];
  count: number;
  skip: number;
  limit: number;
}

export async function createCourse(input: CreateCourseInput) {
  return post<Course>('/courses', input);
}

export async function listCourses() {
  return get<ListCoursesResponse>('/courses');
}

export async function getCourse(id: string) {
  return get<Course>(`/courses/${id}`);
}

export async function getAnalysis(id: string): Promise<{ analysis?: Analysis; course_id: string }> {
  try {
    return await get<{ analysis?: Analysis; course_id: string }>(`/courses/${id}/analysis`);
  } catch (e) {
    if (isNotFoundError(e)) return { analysis: undefined, course_id: id };
    throw e;
  }
}

export async function triggerAnalysis(id: string) {
  return post<{
    analysis?: Analysis;
    course?: Course;
    course_id: string;
    cached?: boolean;
    synthetic?: boolean;
  }>(`/courses/${id}/analyze`);
}

export async function getPedagogical(id: string): Promise<{ pedagogical_design?: PedagogicalDesign; course_id: string }> {
  try {
    return await get<{ pedagogical_design?: PedagogicalDesign; course_id: string }>(
      `/courses/${id}/pedagogical-design`
    );
  } catch (e) {
    if (isNotFoundError(e)) return { pedagogical_design: undefined, course_id: id };
    throw e;
  }
}

export async function triggerPedagogical(id: string) {
  return post<{
    pedagogical_design?: PedagogicalDesign;
    course?: Course;
    course_id: string;
    cached?: boolean;
  }>(`/courses/${id}/pedagogical-design`);
}

export async function getScript(id: string): Promise<{ script?: Script; course_id: string }> {
  try {
    return await get<{ script?: Script; course_id: string }>(`/courses/${id}/script`);
  } catch (e) {
    if (isNotFoundError(e)) return { script: undefined, course_id: id };
    throw e;
  }
}

export async function triggerScript(id: string) {
  return post<{
    script?: Script;
    course?: Course;
    scenes_created?: number;
    cached?: boolean;
  }>(`/courses/${id}/script`);
}

export interface GenerateVideoOptions {
  provider?: string;
}

export async function triggerGenerateVideo(
  id: string,
  provider?: string,
) {
  const body: { provider?: string } = {};
  if (provider && provider.length > 0) body.provider = provider;
  return post<unknown>(`/courses/${id}/generate-video`, Object.keys(body).length > 0 ? body : undefined);
}

export async function getVideo(id: string): Promise<VideoInfo> {
  try {
    const raw = await get<{
      id: string;
      video_url?: string;
      thumbnail_url?: string;
      duration?: number;
      status?: string;
      provider?: string;
      provider_video_id?: string;
      lesson_id?: string;
    }>(`/videos/courses/${id}/latest`);
    return {
      id: raw.id,
      url: raw.video_url,
      thumbnail_url: raw.thumbnail_url,
      duration: raw.duration,
      status: raw.status,
      provider: raw.provider,
      provider_video_id: raw.provider_video_id,
      course_id: id,
    };
  } catch (e) {
    if (isNotFoundError(e)) return { id: '', course_id: id };
    throw e;
  }
}

export async function pollVideoStatus(videoId: string): Promise<VideoInfo | null> {
  try {
    const raw = await get<{
      video_url?: string;
      thumbnail_url?: string;
      duration?: number;
      status?: string;
      progress?: number;
      message?: string;
      provider_video_id?: string;
    }>(`/videos/${videoId}/status`);
    return {
      id: videoId,
      url: raw.video_url,
      thumbnail_url: raw.thumbnail_url,
      duration: typeof raw.duration === 'number' ? raw.duration : undefined,
      status: raw.status,
      provider_video_id: raw.provider_video_id,
      course_id: '',
    };
  } catch (e) {
    if (isNotFoundError(e)) return null;
    throw e;
  }
}

export async function getQA(id: string): Promise<{ qa?: QAResult; course_id: string }> {
  try {
    return await get<{ qa?: QAResult; course_id: string }>(`/courses/${id}/qa`);
  } catch (e) {
    if (isNotFoundError(e)) return { qa: undefined, course_id: id };
    throw e;
  }
}

export async function triggerQAReview(id: string) {
  return post<{
    qa?: QAResult;
    course?: Course;
    cached?: boolean;
  }>(`/courses/${id}/qa-review`);
}

export interface ProcessOptions {
  provider?: string;
  skip_qa?: boolean;
  auto_approve_script?: boolean;
  run_async?: boolean;
}

export async function triggerProcess(
  id: string,
  opts: ProcessOptions = {
    skip_qa: false,
    auto_approve_script: true,
    run_async: false,
  },
) {
  const body: any = {
    skip_qa: opts.skip_qa ?? false,
    auto_approve_script: opts.auto_approve_script ?? true,
    run_async: opts.run_async ?? false,
  };
  if (opts.provider && opts.provider.length > 0) body.provider = opts.provider;
  return post<unknown>(`/workflow/courses/${id}/process`, body);
}

export async function analyzeCourse(id: string) {
  return triggerAnalysis(id);
}

export async function generateScript(id: string) {
  return triggerScript(id);
}

export async function approveScript(id: string) {
  return post<{ approved: boolean; course?: Course; course_id: string }>(`/courses/${id}/approve-script`);
}

export async function regenerateScript(id: string) {
  return triggerScript(id);
}

export async function generateVideo(id: string) {
  return triggerGenerateVideo(id);
}

export async function getCourseStatus(id: string) {
  return get<CourseStatus>(`/courses/${id}/status`);
}

