import ObjectivesList from './ObjectivesList';
import ConceptsList from './ConceptsList';
import StatusBadge from './StatusBadge';

export interface AnalysisData {
  title: string;
  subject: string;
  level: string;
  language: string;
  summary: string;
  main_topics: string[];
  prerequisites: string[];
  concepts: Array<{ concept: string; description: string; source_pages?: number[] }>;
  keywords: string[];
  objectives?: string[];
  estimated_duration_minutes?: number;
}

export default function AnalysisViewer({ analysis }: { analysis: AnalysisData }) {
  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
          <div>
            <h2 className="text-xl font-bold text-slate-900">{analysis.title}</h2>
            <p className="text-slate-500">{analysis.subject} · {analysis.language.toUpperCase()}</p>
          </div>
          <StatusBadge status="ANALYZING" />
        </div>

        <dl className="grid sm:grid-cols-3 gap-4 text-sm mb-6">
          <div className="rounded-lg bg-slate-50 p-3">
            <dt className="text-slate-500 mb-1">Nivel</dt>
            <dd className="font-semibold capitalize text-slate-900">{analysis.level}</dd>
          </div>
          <div className="rounded-lg bg-slate-50 p-3">
            <dt className="text-slate-500 mb-1">Temas</dt>
            <dd className="font-semibold text-slate-900">{analysis.main_topics?.length || 0}</dd>
          </div>
          <div className="rounded-lg bg-slate-50 p-3">
            <dt className="text-slate-500 mb-1">Duración estimada</dt>
            <dd className="font-semibold text-slate-900">
              {analysis.estimated_duration_minutes || 10} min
            </dd>
          </div>
        </dl>

        <div>
          <h3 className="font-semibold text-slate-900 mb-2">Resumen</h3>
          <p className="text-slate-700 leading-relaxed">{analysis.summary}</p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="font-semibold text-slate-900 mb-4">Requisitos previos</h3>
          {analysis.prerequisites?.length ? (
            <ul className="space-y-2">
              {analysis.prerequisites.map((p, i) => (
                <li key={i} className="flex gap-2 text-sm text-slate-700">
                  <span className="text-brand-600 mt-0.5">•</span>
                  {p}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500">No se detectaron requisitos previos.</p>
          )}
        </div>

        <div className="card">
          <h3 className="font-semibold text-slate-900 mb-4">Temas principales</h3>
          <div className="flex flex-wrap gap-2">
            {(analysis.main_topics || []).map((t, i) => (
              <span key={i} className="badge bg-brand-100 text-brand-700">
                {t}
              </span>
            ))}
          </div>
        </div>

        {analysis.objectives && (
          <div className="card md:col-span-2">
            <h3 className="font-semibold text-slate-900 mb-4">Objetivos de aprendizaje</h3>
            <ObjectivesList objectives={analysis.objectives} />
          </div>
        )}

        <div className="card md:col-span-2">
          <h3 className="font-semibold text-slate-900 mb-4">Conceptos clave</h3>
          <ConceptsList concepts={analysis.concepts || []} />
        </div>
      </div>
    </div>
  );
}
