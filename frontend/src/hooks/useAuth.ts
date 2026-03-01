"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { http } from "@/services/http";

type User = {
  id: number;
  nome: string;
  email: string;
  tipo: "produtor" | "comprador" | "admin";
  conta_validada: boolean;
};

const fetcher = async (url: string) => {
  const res = await http.get(url);
  return res.data;
};

export function useAuth(requireAuth = true) {
  const router = useRouter();
  const { data, error, isLoading } = useSWR<{ user: User }>("/auth/me", fetcher, {
    shouldRetryOnError: false,
    revalidateOnFocus: false,
  });

  useEffect(() => {
    if (!isLoading && requireAuth && (error || !data?.user)) {
      router.push("/auth/login");
    }
  }, [data, error, isLoading, requireAuth, router]);

  return {
    user: data?.user,
    isLoading,
    isAuthenticated: !!data?.user,
  };
}
