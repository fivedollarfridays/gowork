export async function ocrPdfText(file: File): Promise<string> {
  // Dynamic import to keep tesseract.js out of the main bundle (~15MB WASM)
  const { createWorker } = await import("tesseract.js");
  const worker = await createWorker("eng");

  try {
    const buffer = await file.arrayBuffer();
    const blob = new Blob([buffer], { type: "application/pdf" });
    const { data } = await worker.recognize(blob);
    return data.text.trim();
  } finally {
    await worker.terminate();
  }
}
