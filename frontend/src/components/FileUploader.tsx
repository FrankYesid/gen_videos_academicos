import { useState, useCallback, useEffect, DragEvent, ChangeEvent } from 'react';
import { CloudArrowUpIcon, XMarkIcon, CheckCircleIcon, DocumentIcon } from '@heroicons/react/24/outline';
import { uploadDocument, Document } from '../services/documents';

export interface FileInfo {
  name: string;
  size: number;
  type: string;
  status: 'idle' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
  raw?: File;
  document?: Document;
}

interface FileUploaderProps {
  value?: FileInfo | null;
  onChange?: (info: FileInfo | null) => void;
  className?: string;
  label?: string;
}

export default function FileUploader({
  value,
  onChange,
  className = '',
  label = 'Documento PDF',
}: FileUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [internal, setInternal] = useState<FileInfo | null>(value ?? null);

  useEffect(() => {
    if (value !== undefined) setInternal(value);
  }, [value]);

  const commit = (info: FileInfo | null) => {
    setInternal(info);
    onChange?.(info);
  };

  const validateFile = (file: File): string | null => {
    const maxSizeMB = 50;
    if (file.type !== 'application/pdf') return 'Solo se permiten archivos PDF.';
    if (file.size > maxSizeMB * 1024 * 1024)
      return `El archivo excede el límite de ${maxSizeMB} MB.`;
    return null;
  };

  const handleFile = useCallback(
    async (file: File) => {
      const error = validateFile(file);
      const initial: FileInfo = {
        name: file.name,
        size: file.size,
        type: file.type,
        status: error ? 'error' : 'uploading',
        progress: 0,
        error: error || undefined,
        raw: file,
      };
      commit(initial);

      if (!error) {
        try {
          const doc = await uploadDocument(file, (p) =>
            commit({ ...initial, progress: p, status: p >= 100 ? 'success' : 'uploading' })
          );
          commit({
            ...initial,
            status: 'success',
            progress: 100,
            document: doc,
          });
        } catch (e: any) {
          const msg =
            e?.response?.data?.detail || e?.message || 'Error al subir el documento';
          commit({
            ...initial,
            status: 'error',
            error: typeof msg === 'string' ? msg : 'Error desconocido',
          });
        }
      }
    },
    [commit]
  );

  const onDrop = (e: DragEvent<HTMLElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) void handleFile(file);
  };

  const onChangeInput = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (file) void handleFile(file);
  };

  const removeFile = () => commit(null);

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  return (
    <div className={`card ${className}`}>
      <h3 className="font-semibold text-slate-900 mb-4">{label}</h3>

      {!internal ? (
        <label
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={onDrop}
          className={`block border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-200 ${
            isDragging
              ? 'border-brand-500 bg-brand-50 scale-[1.01]'
              : 'border-slate-300 hover:border-brand-400 hover:bg-slate-50'
          }`}
        >
          <input type="file" accept="application/pdf" className="hidden" onChange={onChangeInput} />
          <CloudArrowUpIcon className="w-14 h-14 mx-auto text-brand-500 mb-4 drop-shadow-sm" />
          <p className="text-slate-800 font-semibold mb-1 text-base">
            Arrastra y suelta tu PDF aquí
          </p>
          <p className="text-sm text-slate-500 mb-5">o haz clic para seleccionar un archivo</p>
          <span className="btn btn-upload btn-sm inline-flex">
            <CloudArrowUpIcon className="w-4 h-4" />
            Seleccionar PDF
          </span>
          <p className="text-xs text-slate-400 mt-4">Máximo 50 MB · Formato PDF</p>
        </label>
      ) : (
        <div
          className={`flex items-center gap-4 p-4 rounded-xl border ${
            internal.status === 'error'
              ? 'bg-rose-50 border-rose-300'
              : internal.status === 'success'
              ? 'bg-emerald-50 border-emerald-300'
              : 'bg-brand-50 border-brand-200'
          }`}
        >
          <div
            className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${
              internal.status === 'error'
                ? 'bg-rose-100 text-rose-600'
                : internal.status === 'success'
                ? 'bg-emerald-100 text-emerald-700'
                : 'bg-brand-100 text-brand-700'
            }`}
          >
            {internal.status === 'success' ? (
              <CheckCircleIcon className="w-7 h-7" />
            ) : (
              <DocumentIcon className="w-7 h-7" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-slate-900 truncate">{internal.name}</p>
            <p className="text-xs text-slate-500">
              {formatSize(internal.size)} · {internal.type}
              {internal.document?.page_count
                ? ` · ${internal.document.page_count} páginas`
                : ''}
            </p>
            {internal.status === 'error' ? (
              <p className="text-xs text-rose-600 mt-1 font-medium">{internal.error}</p>
            ) : (
              <div className="mt-2 h-2.5 w-full bg-slate-200 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-300 ${
                    internal.status === 'success' ? 'bg-emerald-500' : 'bg-brand-600'
                  }`}
                  style={{ width: `${internal.progress}%` }}
                />
              </div>
            )}
            {internal.status === 'uploading' && (
              <p className="text-xs text-slate-600 mt-1.5">
                Subiendo archivo... {internal.progress}%
              </p>
            )}
            {internal.status === 'success' && (
              <p className="text-xs text-emerald-700 mt-1.5 font-medium">
                ✅ Documento cargado correctamente
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={removeFile}
            disabled={internal.status === 'uploading'}
            className="shrink-0 p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors disabled:opacity-40"
            title="Quitar archivo"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>
      )}
    </div>
  );
}
