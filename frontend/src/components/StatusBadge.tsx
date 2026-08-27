export default function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    CREATED: 'bg-slate-100 text-slate-700',
    UPLOADED: 'bg-sky-100 text-sky-700',
    EXTRACTING: 'bg-sky-100 text-sky-700',
    ANALYZING: 'bg-violet-100 text-violet-700',
    PEDAGOGICAL_DESIGN: 'bg-violet-100 text-violet-700',
    SCRIPT_GENERATED: 'bg-amber-100 text-amber-700',
    SCRIPT_VALIDATED: 'bg-amber-100 text-amber-700',
    VIDEO_GENERATING: 'bg-orange-100 text-orange-700',
    VIDEO_PROCESSING: 'bg-orange-100 text-orange-700',
    VIDEO_READY: 'bg-emerald-100 text-emerald-700',
    QA: 'bg-emerald-100 text-emerald-700',
    COMPLETED: 'bg-emerald-100 text-emerald-700',
    FAILED: 'bg-rose-100 text-rose-700',
  };
  const style = styles[status] || styles.CREATED;
  const label = status.replace(/_/g, ' ').toLowerCase();
  return (
    <span className={`badge ${style} capitalize`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-60" />
      {label}
    </span>
  );
}
