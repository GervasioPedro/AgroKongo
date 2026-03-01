import { cookies } from "next/headers";

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

  const res = await fetch(`${BACKEND_BASE_URL}/api/produtor/dashboard`, {
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
    return Response.json(
      { error: "Falha ao carregar dashboard do produtor" },
      { status: res.status }
    );
  }

  const data = await res.json();
  return Response.json(data);
}
