export type FileType = "pdf" | "docx" | "txt";

export type ExtractionMethod = "native" | "ocr" | "docx" | "plaintext";

export interface ExtractionResult {
  text: string;
  method: ExtractionMethod;
  confidence: number;
  wordCount: number;
}
