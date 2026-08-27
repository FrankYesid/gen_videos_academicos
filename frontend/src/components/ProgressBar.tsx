export default function ProgressBar({ progress }: { progress: number }) {
  const clamped = Math.max(0, Math.min(100, progress));
  return (
    <div className="w-full">
      <div className="flex justify-between text-xs text-slate-300 mb-2">
        <span>Progreso</span>
        <span>{clamped}%</span>
      </div>
      <div className="h-3 w-full bg-slate-800 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-brand-500 to-brand-400 transition-all duration-500"
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
