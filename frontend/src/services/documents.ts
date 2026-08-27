import { api, get, del } from './api';

export interface Document {
  id: string;
  filename: string;
  original_filename: string;
  content_type: string;
  file_size_bytes?: number;
  page_count?: number;
  status: 'pending' | 'extracting' | 'ready' | 'error';
  uploaded_at?: string;
  extracted_text_preview?: string;
}

export interface ListDocumentsResponse {
  items: Document[];
  count: number;
  skip: number;
  limit: number;
}

export async function uploadDocument(file: File, onProgress?: (percent: number) => void): Promise<Document> {
  const formData = new FormData();
  formData.append('file', file);

  const { data } = await api.post<{ success: boolean; data: Document }>(
    '/documents/upload',
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (event: any) => {
        if (onProgress && event?.total) {
          onProgress(Math.round((event.loaded * 100) / event.total));
        }
      },
      timeout: 120_000,
    }
  );

  if (!data.success) {
    const err = (data as any)?.error;
    throw new Error(err?.message || 'Error al subir el documento');
  }
  return data.data;
}

export async function listDocuments(params?: { skip?: number; limit?: number }) {
  return get<ListDocumentsResponse>(
    `/documents?skip=${params?.skip ?? 0}&limit=${params?.limit ?? 50}`
  );
}

export async function getDocument(id: string): Promise<Document> {
  return get<Document>(`/documents/${id}`);
}

export async function deleteDocument(id: string): Promise<void> {
  return del<void>(`/documents/${id}`);
}
