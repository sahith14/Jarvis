export interface AIResponse {
  action: string;
  message?: string;
  [key: string]: any;
}

export interface WebSocketMessage {
  type: string;
  data?: any;
  path?: string;
  content?: string;
  old_content?: string;
  new_content?: string;
  diff?: string;
}

export interface PendingEdit {
  path: string;
  oldContent: string;
  newContent: string;
  diff: string;
}
