export interface Scene {
  id: number;
  title: string;
  duration_seconds: number;
  narration: string;
  visual_instruction: string;
  on_screen_text: string;
  educational_purpose: string;
  camera_angle?: string;
  background?: string;
  audio_cue?: string;
}

export interface Script {
  title: string;
  scenes: Scene[];
  total_duration_seconds: number;
  introduction: string;
  conclusion: string;
  target_audience: string;
  tone: string;
  notes?: string;
}

export type ScriptOutput = Script;
