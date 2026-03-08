import type { ExtractionResult, FileType } from "./types";
import { extractPdfText } from "./pdf";
import { ocrPdfText } from "./ocr";
import { extractDocxText } from "./docx";

const MIN_NATIVE_WORDS = 50;

function countWords(text: string): number {
  return text.split(/\s+/).filter(Boolean).length;
}

export function detectFileType(file: File): FileType {
  const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
  const mime = file.type.toLowerCase();

  if (ext === "pdf" || mime === "application/pdf") return "pdf";
  if (
    ext === "docx" ||
    mime === "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
  )
    return "docx";
  return "txt";
}

async function readPlainText(file: File): Promise<string> {
  return file.text();
}

export async function extractResumeText(
  file: File,
): Promise<ExtractionResult> {
  const fileType = detectFileType(file);

  if (fileType === "txt") {
    const text = await readPlainText(file);
    return {
      text,
      method: "plaintext",
      confidence: 1.0,
      wordCount: countWords(text),
    };
  }

  if (fileType === "docx") {
    try {
      const text = await extractDocxText(file);
      return {
        text,
        method: "docx",
        confidence: 0.9,
        wordCount: countWords(text),
      };
    } catch {
      return { text: "", method: "docx", confidence: 0, wordCount: 0 };
    }
  }

  // PDF: try native first, fall back to OCR
  try {
    const nativeText = await extractPdfText(file);
    const wordCount = countWords(nativeText);

    if (wordCount >= MIN_NATIVE_WORDS) {
      return {
        text: nativeText,
        method: "native",
        confidence: 0.95,
        wordCount,
      };
    }

    // Too few words — likely a scanned PDF, try OCR
    try {
      const ocrText = await ocrPdfText(file);
      const ocrWordCount = countWords(ocrText);
      return {
        text: ocrText,
        method: "ocr",
        confidence: 0.7,
        wordCount: ocrWordCount,
      };
    } catch {
      // OCR failed, return whatever native extraction got
      return {
        text: nativeText,
        method: "native",
        confidence: wordCount > 0 ? 0.3 : 0,
        wordCount,
      };
    }
  } catch {
    return { text: "", method: "native", confidence: 0, wordCount: 0 };
  }
}
