import { EyeIcon, MicrophoneIcon, DocumentTextIcon, SparklesIcon } from '@heroicons/react/24/outline';

interface Scene {
  id: number;
  title: string;
  duration_seconds: number;
  narration: string;
  visual_instruction: string;
  on_screen_text: string;
  educational_purpose: string;
}

export default function SceneCard({ scene }: { scene: Scene }) {
  const purposeIcons: Record<string, typeof EyeIcon> = {
    introduction: SparklesIcon,
  };
  const Icon = purposeIcons[scene.educational_purpose?.toLowerCase()] || DocumentTextIcon;

  return (
    <div className="card">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex items-center gap-3">
          <span className="w-10 h-10 rounded-lg bg-brand-100 text-brand-700 flex items-center justify-center font-bold text-sm shrink-0">
            {scene.id}
          </span>
          <div>
            <h3 className="font-semibold text-slate-900">{scene.title}</h3>
            <p className="text-xs text-slate-500">
              Duración: {scene.duration_seconds}s · Propósito:{' '}
              <span className="capitalize">{scene.educational_purpose}</span>
            </p>
          </div>
        </div>
        <Icon className="w-5 h-5 text-slate-400 shrink-0" />
      </div>

      <div className="grid md:grid-cols-2 gap-4 text-sm">
        <div className="p-3 rounded-lg bg-slate-50">
          <div className="flex items-center gap-1 text-slate-500 text-xs font-medium mb-2">
            <MicrophoneIcon className="w-3.5 h-3.5" />
            Narración
          </div>
          <p className="text-slate-700 leading-relaxed italic">{scene.narration}</p>
        </div>
        <div className="space-y-3">
          <div className="p-3 rounded-lg bg-slate-50">
            <div className="flex items-center gap-1 text-slate-500 text-xs font-medium mb-2">
              <EyeIcon className="w-3.5 h-3.5" />
              Instrucción visual
            </div>
            <p className="text-slate-700 leading-relaxed">{scene.visual_instruction}</p>
          </div>
          <div className="p-3 rounded-lg border border-dashed border-slate-300 bg-white">
            <div className="text-slate-500 text-xs font-medium mb-1">Texto en pantalla</div>
            <p className="text-slate-700 leading-relaxed">{scene.on_screen_text}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
