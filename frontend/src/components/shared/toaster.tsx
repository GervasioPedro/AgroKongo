"use client";

import { Toaster } from "react-hot-toast";

export function AppToaster() {
  return (
    <Toaster
      position="top-center"
      toastOptions={{
        duration: 4000,
        style: {
          borderRadius: "14px",
          background: "#FFFFFF",
          color: "#0f172a",
          boxShadow: "0 10px 30px rgba(0,0,0,0.08)"
        },
        success: {
          iconTheme: { primary: "#1B5E20", secondary: "#F0F4F0" }
        },
        error: {
          iconTheme: { primary: "#F57C00", secondary: "#FFFFFF" }
        }
      }}
    />
  );
}
