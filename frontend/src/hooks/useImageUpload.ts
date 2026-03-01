"use client";

import { useState } from "react";
import { compressImage } from "@/utils/image-compression";

export function useImageUpload() {
  const [isCompressing, setIsCompressing] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleImageUpload = async (file: File): Promise<File> => {
    setIsCompressing(true);
    setProgress(0);

    try {
      const interval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 10, 90));
      }, 100);

      const compressed = await compressImage(file);
      
      clearInterval(interval);
      setProgress(100);
      
      return compressed;
    } finally {
      setTimeout(() => {
        setIsCompressing(false);
        setProgress(0);
      }, 500);
    }
  };

  return { handleImageUpload, isCompressing, progress };
}
