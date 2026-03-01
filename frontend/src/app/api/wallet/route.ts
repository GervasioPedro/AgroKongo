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
  } catch {
    // Fallback DEV (backend offline)
    return Response.json({
      resumo: {
        saldoDisponivelKz: 125000,
        saldoEscrowKz: 35000,
        pendentes: 2
      },
      movimentos: [
        {
          id: "m1",
          tipo: "credito",
          valorKz: 50000,
          descricao: "Pagamento recebido (Escrow)",
          createdAtISO: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString()
        },
        {
          id: "m2",
          tipo: "escrow",
          valorKz: 35000,
          descricao: "Valor em escrow (dinheiro seguro)",
          createdAtISO: new Date(Date.now() - 1000 * 60 * 60 * 20).toISOString()
        },
        {
          id: "m3",
          tipo: "debito",
          valorKz: 15000,
          descricao: "Retirada para IBAN",
          createdAtISO: new Date(Date.now() - 1000 * 60 * 60 * 30).toISOString()
        }
      ]
    } satisfies WalletPayload);
  }
}
