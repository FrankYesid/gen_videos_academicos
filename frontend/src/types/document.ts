export interface Document {
  id: string;
  filename: string;
  file_size: number;
  mime_type: string;
  page_count?: number;
  extracted_text?: string;
  status: string;
  created_at: string;
  updated_at: string;
}
