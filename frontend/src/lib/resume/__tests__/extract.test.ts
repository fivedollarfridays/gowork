import { describe, it, expect, vi, beforeEach } from "vitest";
import type { ExtractionResult } from "../types";

// Mock the sub-modules before importing extract
vi.mock("../pdf", () => ({
  extractPdfText: vi.fn(),
}));
vi.mock("../ocr", () => ({
  ocrPdfText: vi.fn(),
}));
vi.mock("../docx", () => ({
  extractDocxText: vi.fn(),
}));

import { extractResumeText, detectFileType } from "../extract";
import { extractPdfText } from "../pdf";
import { ocrPdfText } from "../ocr";
import { extractDocxText } from "../docx";

function makeFile(name: string, content: string, type = ""): File {
  return new File([content], name, { type });
}

describe("detectFileType", () => {
  it("detects PDF by extension", () => {
    expect(detectFileType(makeFile("resume.pdf", ""))).toBe("pdf");
  });

  it("detects PDF by MIME type", () => {
    expect(detectFileType(makeFile("resume", "", "application/pdf"))).toBe("pdf");
  });

  it("detects DOCX by extension", () => {
    expect(detectFileType(makeFile("resume.docx", ""))).toBe("docx");
  });

  it("detects DOCX by MIME type", () => {
    const mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
    expect(detectFileType(makeFile("resume", "", mime))).toBe("docx");
  });

  it("detects TXT by extension", () => {
    expect(detectFileType(makeFile("resume.txt", ""))).toBe("txt");
  });

  it("defaults to txt for unknown types", () => {
    expect(detectFileType(makeFile("resume", ""))).toBe("txt");
  });

  it("is case-insensitive for extension", () => {
    expect(detectFileType(makeFile("resume.PDF", ""))).toBe("pdf");
    expect(detectFileType(makeFile("resume.Docx", ""))).toBe("docx");
  });
});

describe("extractResumeText", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("extracts text from PDF using native extraction", async () => {
    const pdfMock = vi.mocked(extractPdfText);
    pdfMock.mockResolvedValue(
      "Software engineer with 5 years experience in healthcare systems and patient management. " +
      "Proficient in Python, JavaScript, and SQL. Developed internal tools for data analytics. " +
      "Led a team of 3 developers on a web application for scheduling and resource allocation. " +
      "Strong communication skills and ability to work independently in fast-paced environments. " +
      "Bachelor of Science in Computer Science from Auburn University Montgomery. Certified in AWS.",
    );

    const result = await extractResumeText(makeFile("resume.pdf", "fake-pdf-bytes"));

    expect(pdfMock).toHaveBeenCalled();
    expect(result.method).toBe("native");
    expect(result.wordCount).toBeGreaterThan(10);
    expect(result.confidence).toBeGreaterThanOrEqual(0.8);
    expect(result.text).toContain("Software engineer");
  });

  it("falls back to OCR when native PDF extraction yields few words", async () => {
    const pdfMock = vi.mocked(extractPdfText);
    const ocrMock = vi.mocked(ocrPdfText);
    pdfMock.mockResolvedValue("header only");
    ocrMock.mockResolvedValue("Full resume text extracted via OCR from a scanned document with sufficient words to pass the threshold check easily");

    const result = await extractResumeText(makeFile("resume.pdf", "scanned-pdf"));

    expect(pdfMock).toHaveBeenCalled();
    expect(ocrMock).toHaveBeenCalled();
    expect(result.method).toBe("ocr");
    expect(result.wordCount).toBeGreaterThan(10);
  });

  it("uses native result even with few words when OCR fails", async () => {
    const pdfMock = vi.mocked(extractPdfText);
    const ocrMock = vi.mocked(ocrPdfText);
    pdfMock.mockResolvedValue("short text");
    ocrMock.mockRejectedValue(new Error("OCR failed"));

    const result = await extractResumeText(makeFile("resume.pdf", "data"));

    expect(result.method).toBe("native");
    expect(result.text).toBe("short text");
    expect(result.confidence).toBeLessThan(0.5);
  });

  it("extracts text from DOCX", async () => {
    const docxMock = vi.mocked(extractDocxText);
    docxMock.mockResolvedValue("My work experience includes warehouse management and forklift operation");

    const result = await extractResumeText(makeFile("resume.docx", "docx-bytes"));

    expect(docxMock).toHaveBeenCalled();
    expect(result.method).toBe("docx");
    expect(result.confidence).toBe(0.9);
    expect(result.text).toContain("warehouse management");
  });

  it("extracts text from plain text file", async () => {
    const content = "I have worked as a cashier for 3 years at various retail stores";
    const file = makeFile("resume.txt", content);

    const result = await extractResumeText(file);

    expect(result.method).toBe("plaintext");
    expect(result.confidence).toBe(1.0);
    expect(result.text).toBe(content);
    expect(result.wordCount).toBe(13);
  });

  it("handles empty files gracefully", async () => {
    const file = makeFile("empty.txt", "");

    const result = await extractResumeText(file);

    expect(result.text).toBe("");
    expect(result.wordCount).toBe(0);
    expect(result.confidence).toBe(1.0);
  });

  it("handles PDF extraction error gracefully", async () => {
    const pdfMock = vi.mocked(extractPdfText);
    pdfMock.mockRejectedValue(new Error("Corrupt PDF"));

    const result = await extractResumeText(makeFile("bad.pdf", "corrupt"));

    expect(result.text).toBe("");
    expect(result.wordCount).toBe(0);
    expect(result.confidence).toBe(0);
    expect(result.method).toBe("native");
  });

  it("handles DOCX extraction error gracefully", async () => {
    const docxMock = vi.mocked(extractDocxText);
    docxMock.mockRejectedValue(new Error("Bad DOCX"));

    const result = await extractResumeText(makeFile("bad.docx", "corrupt"));

    expect(result.text).toBe("");
    expect(result.wordCount).toBe(0);
    expect(result.confidence).toBe(0);
    expect(result.method).toBe("docx");
  });

  it("counts words correctly", async () => {
    const text = "one two  three\nfour\tfive";
    const file = makeFile("resume.txt", text);

    const result = await extractResumeText(file);

    expect(result.wordCount).toBe(5);
  });
});
