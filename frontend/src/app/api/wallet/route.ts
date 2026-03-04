import { cookies } from "next/headers";

type WalletResumo = {
  saldoDisponivelKz: number;
  saldoEscrowKz: number;
  pendentes: number;
};

type Movimento = {
  id: string;
  tipo: "credito" | "debito" | "escrow" | string;
  valorKz: number;
  descricao: string;
  createdAtISO: string | null;
};

type WalletPayload = {
  resumo: WalletResumo;
  movimentos: Movimento[];
};

const BACKEND_BASE_URL = process.env.BACKEND_BASE_URL || "http://127.0.0.1:5000";

// Proteção SSRF: validar URL do backend
if (!BACKEND_BASE_URL.startsWith("http://127.0.0.1") && !BACKEND_BASE_URL.startsWith("http://localhost") && !BACKEND_BASE_URL.startsWith("https://")) {
  throw new Error("URL do backend inválida");
}

export async function GET() {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join("; ");

  try {
    const res = await fetch(`${BACKEND_BASE_URL}/api/wallet`, {
      method: "GET",
      headers: {
        Accept: "application/json",
        ...(cookieHeader ? { Cookie: cookieHeader } : {})
      },
      cache: "no-store",
      // Proteção SSRF: desabilitar redirecionamentos
      redirect: "manual"
    });

    if (!res.ok) {
      throw new Error(`Backend respondeu ${res.status}`);
    }

    const data = (await res.json()) as WalletPayload;
    return Response.json(data);
  } catch (error) {
    console.error('Erro ao carregar dados da carteira:', error);
    return Response.json(
      { error: 'Erro ao carregar dados da carteira' },
      { status: 500 }
    );
  }
}
