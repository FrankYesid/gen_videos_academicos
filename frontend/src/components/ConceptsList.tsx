interface Concept {
  concept: string;
  description: string;
  source_pages?: number[];
}

export default function ConceptsList({ concepts }: { concepts: Concept[] }) {
  if (!concepts.length)
    return <p className="text-sm text-slate-500">No se detectaron conceptos aún.</p>;

  return (
    <div className="grid md:grid-cols-2 gap-3">
      {concepts.map((c, i) => (
        <div key={i} className="p-4 rounded-lg border border-slate-200 bg-slate-50/50">
          <div className="flex items-start justify-between gap-2 mb-1">
            <h4 className="font-semibold text-slate-900">{c.concept}</h4>
            {c.source_pages && (
              <span className="text-xs text-slate-500">
                p. {c.source_pages.join(', ')}
              </span>
            )}
          </div>
          <p className="text-sm text-slate-600 leading-relaxed">{c.description}</p>
        </div>
      ))}
    </div>
  );
}
