"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function RegistoPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirecionar para cadastro em etapas
    router.push("/auth/cadastro/passo-1");
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin h-12 w-12 border-4 border-agro-primary border-t-transparent rounded-full mx-auto mb-4"></div>
        <p className="text-slate-600">A redirecionar...</p>
      </div>
    </div>
  );
}
