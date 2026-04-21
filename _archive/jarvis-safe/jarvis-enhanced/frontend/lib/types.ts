export interface AIResponse { action: string; message?: string; [key: string]: any; }
export interface PendingEdit {
  path: string; oldContent: string; newContent: string; diff: string;
  dangerLevel: string; warnings: string[];
}
