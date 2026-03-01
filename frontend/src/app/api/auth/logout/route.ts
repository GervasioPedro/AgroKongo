import { NextResponse } from "next/server";
import { cookies } from "next/headers";

const BACKEND_BASE_URL = process.env.BACKEND_BASE_URL || "http://127.0.0.1:5000";

// Proteção SSRF: validar URL do backend
if (!BACKEND_BASE_URL.startsWith("http://127.0.0.1") && !BACKEND_BASE_URL.startsWith("http://localhost") && !BACKEND_BASE_URL.startsWith("https://")) {
  throw new Error("URL do backend inválida");
}

export async function POST() {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join("; ");

  const res = await fetch(`${BACKEND_BASE_URL}/api/auth/logout`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      ...(cookieHeader ? { Cookie: cookieHeader } : {})
    },
    cache: "no-store",
    // Proteção SSRF: desabilitar redirecionamentos
    redirect: "manual"
  });

  const data = await res.json().catch(() => ({}));
  const nextRes = NextResponse.json(data, { status: res.status });

  const anyRes: any = res;
  const setCookies: string[] =
    typeof anyRes?.headers?.getSetCookie === "function" ? anyRes.headers.getSetCookie() : [];

  if (setCookies.length > 0) {
    for (const c of setCookies) nextRes.headers.append("set-cookie", c);
  } else {
    const setCookie = res.headers.get("set-cookie");
    if (setCookie) nextRes.headers.set("set-cookie", setCookie);
  }

  return nextRes;
}
