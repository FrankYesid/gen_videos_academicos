import { CheckCircleIcon } from '@heroicons/react/24/outline';

export default function ObjectivesList({ objectives }: { objectives: string[] }) {
  return (
    <ol className="space-y-3">
      {objectives.map((obj, i) => (
        <li key={i} className="flex gap-3">
          <div className="shrink-0 mt-0.5">
            <CheckCircleIcon className="w-5 h-5 text-emerald-600" />
          </div>
          <p className="text-sm text-slate-700 leading-relaxed">{obj}</p>
        </li>
      ))}
    </ol>
  );
}
