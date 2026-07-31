"use client";

import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

// react-pdf/pdfjs-dist touch browser-only globals (DOMMatrix, etc.) at module
// import time, which crashes Next.js's server-side prerender pass. This file
// must only ever be loaded client-side — see SlideViewer.tsx's
// next/dynamic(..., { ssr: false }) import of it.
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

type PdfPageProps = {
  fileUrl: string;
  pageNumber: number;
  onLoadSuccess: (numPages: number) => void;
  onLoadError: () => void;
};

export default function PdfPage({ fileUrl, pageNumber, onLoadSuccess, onLoadError }: PdfPageProps) {
  return (
    <Document
      file={fileUrl}
      onLoadSuccess={({ numPages }) => onLoadSuccess(numPages)}
      onLoadError={onLoadError}
      loading={<div className="w-[600px] h-[420px]" />}
    >
      <Page
        pageNumber={pageNumber}
        width={600}
        renderAnnotationLayer={false}
        renderTextLayer={false}
      />
    </Document>
  );
}
