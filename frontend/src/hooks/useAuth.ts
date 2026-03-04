"use client";

import { useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import useSWR, { mutate as globalMutate } from "swr";
import { http } from "@/services/http";

type User = {
  id: number;
  nome: string;
  email: string;
  tipo: "produtor" | "comprador" | "admin";
  conta_validada: boolean;
};

type MeResponse = { ok: boolean; user?: User; message?: string };

const fetcher = async (url: string): Promise<MeResponse> => {
  try {
    const res = await http.get(url);
    return res.data as MeResponse;
  } catch (err: any) {
    // Anexar status para diferenciar 401
    const status = err?.response?.status;
    if (typeof status !== "undefined") {
      err.status = status;
    }
    throw err;
  }
};

export function useAuth(requireAuth = true) {
  const router = useRouter();
  const { data, error, isLoading, mutate } = useSWR<MeResponse>("/auth/me", fetcher, {
    shouldRetryOnError: false,
    revalidateOnFocus: false,
  });

  const errorType = useMemo<"unauthorized" | "network" | null>(() => {
    if (!error) return null;
    // 401 do backend
    if ((error as any)?.status === 401) return "unauthorized";
    return "network";
  }, [error]);

  useEffect(() => {
    if (!isLoading && requireAuth) {
      if (errorType === "unauthorized" || (data && data.ok === false && !data.user)) {
        router.push("/auth/login");
      }
    }
  }, [data, errorType, isLoading, requireAuth, router]);

  return {
    user: data?.user,
    isLoading,
    isAuthenticated: !!data?.user,
    error,
    errorType,
    refresh: () => mutate(),
    mutateMe: () => globalMutate("/auth/me"),
  };
}
