import { cookies } from "next/headers";

const BACKEND_BASE_URL = process.env.BACKEND_BASE_URL || "http://127.0.0.1:5000";

// Proteção SSRF: validar URL do backend
if (!BACKEND_BASE_URL.startsWith("http://127.0.0.1") && !BACKEND_BASE_URL.startsWith("http://localhost") && !BACKEND_BASE_URL.startsWith("https://")) {
  throw new Error("URL do backend inválida");
}

export async function GET(request: Request) {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join("; ");

  const { searchParams } = new URL(request.url);
  const status = searchParams.get("status");

  let url = `${BACKEND_BASE_URL}/minhas-compras`;
  if (status) {
    url += `?status=${status}`;
  }

  try {
    const res = await fetch(url, {
      method: "GET",
      headers: {
        Accept: "application/json",
        ...(cookieHeader ? { Cookie: cookieHeader } : {})
      },
      cache: "no-store",
      redirect: "manual"
    });

    if (!res.ok) {
      throw new Error(`Backend respondeu ${res.status}`);
    }

    const data = await res.json();
    return Response.json(data);
  } catch (error) {
    console.error("Erro ao carregar compras do comprador:", error);
    return Response.json(
      { ok: false, message: "Erro ao carregar compras" },
      { status: 500 }
    );
  }
}
