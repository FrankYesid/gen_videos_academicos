import SceneCard from './SceneCard';

interface Scene {
  id: number;
  title: string;
  duration_seconds: number;
  narration: string;
  visual_instruction: string;
  on_screen_text: string;
  educational_purpose: string;
}

export interface ScriptData {
  title: string;
  scenes: Scene[];
  total_duration_seconds: number;
}

export default function ScriptViewer({ script }: { script: ScriptData }) {
  const total = script.total_duration_seconds || 0;
  const min = Math.floor(total / 60);
  const sec = total % 60;

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
          <div>
            <h2 className="text-xl font-bold text-slate-900 mb-1">{script.title}</h2>
            <p className="text-sm text-slate-500">
              {script.scenes?.length || 0} escenas · Duración estimada: {min}:
              {String(sec).padStart(2, '0')}
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {(script.scenes || []).map((scene) => (
          <SceneCard key={scene.id} scene={scene} />
        ))}
      </div>
    </div>
  );
}
