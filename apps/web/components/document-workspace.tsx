"use client";

import { useState } from "react";

import { DocumentList } from "@/components/document-list";
import { DocumentUpload } from "@/components/document-upload";

export function DocumentWorkspace() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <>
      <DocumentUpload onUploadComplete={() => setRefreshKey((value) => value + 1)} />
      <DocumentList refreshKey={refreshKey} />
    </>
  );
}
