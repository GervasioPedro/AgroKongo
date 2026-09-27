/**
 * Cliente HTTP central do AgroKongo (React SPA → API Django/DRF).
 *
 * Substitui os ~20 fetch() espalhados pelas páginas, que apontavam para o
 * backend Flask antigo (localhost:5000). Tudo passa por aqui e aponta para o
 * Django em /api/v1 (configurável via NEXT_PUBLIC_API_URL).
 */

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

const TOKEN_KEY = "agrokongo_token";
const USER_KEY = "agrokongo_user";

/* ---------------- sessão local ---------------- */

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setSession(token: string, user: Utilizador) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getUsuario(): Utilizador | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  return raw ? (JSON.parse(raw) as Utilizador) : null;
}

/* ---------------- tipos ---------------- */

export interface Utilizador {
  id: number;
  nome: string;
  telemovel: string;
  email?: string | null;
  tipo: "comprador" | "produtor" | "admin";
  nif?: string | null;
  iban?: string | null;
  rating_vendedor: string;
  vendas_concluidas: number;
  perfil_completo: boolean;
  conta_validada: boolean;
  provincia?: number | null;
  municipio?: number | null;
}

export interface Safra {
  id: number;
  produto: number;
  produto_nome: string;
  categoria: string;
  quantidade_disponivel: string;
  unidade: string;
  preco_por_unidade: string;
  status: "disponivel" | "reservada" | "vendida" | "retirada";
  imagem_url?: string | null;
  observacoes?: string | null;
  produtor: number;
  produtor_nome: string;
  produtor_rating: string;
  localizacao: string;
  valor_estimado: string;
  criado_em: string;
}

export interface Transacao {
  id: number;
  safra: number;
  comprador: number;
  vendedor: number;
  quantidade: string;
  valor_total: string;
  comissao_plataforma: string;
  valor_liquido_vendedor: string;
  status: string;
  codigo: string;
  criado_em: string;
}

/* ---------------- erro + request ---------------- */

export class ApiError extends Error {
  status: number;
  detalhes: Record<string, unknown>;

  constructor(status: number, message: string, detalhes: object = {}) {
    super(message);
    this.status = status;
    this.detalhes = detalhes as Record<string, unknown>;
  }
}

async function request<T = unknown>(
  path: string,
  options: RequestInit & { auth?: boolean } = {}
): Promise<T> {
  const { auth = true, headers, ...rest } = options;
  const finalHeaders: Record<string, string> = {
    ...(headers as Record<string, string>),
  };

  const isForm = rest.body instanceof FormData;
  if (!isForm && rest.body) finalHeaders["Content-Type"] = "application/json";
  if (auth) {
    const token = getToken();
    if (token) finalHeaders["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, { ...rest, headers: finalHeaders });

  if (res.status === 401 && typeof window !== "undefined") {
    clearSession();
  }

  if (res.status === 204) return undefined as T;

  let json: any = null;
  try {
    json = await res.json();
  } catch {
    /* resposta sem corpo JSON */
  }

  if (!res.ok) {
    const mensagem =
      json?.erro ||
      json?.detail ||
      (json && typeof json === "object"
        ? Object.values(json).flat()[0]
        : null) ||
      `Erro ${res.status}`;
    throw new ApiError(res.status, String(mensagem), json ?? {});
  }
  return json as T;
}

/* ---------------- endpoints ---------------- */

export const api = {
  /* autenticação — Django responde { token, utilizador } */
  login: async (telemovel: string, senha: string) => {
    const data = await request<{ token: string; utilizador: Utilizador }>("/auth", {
      method: "POST",
      auth: false,
      body: JSON.stringify({ acao: "login", telemovel, senha }),
    });
    setSession(data.token, data.utilizador);
    return data.utilizador;
  },

  registo: async (payload: {
    nome: string;
    telemovel: string;
    senha: string;
    tipo: "comprador" | "produtor";
  }) => {
    const data = await request<{ token: string; utilizador: Utilizador }>("/auth", {
      method: "POST",
      auth: false,
      body: JSON.stringify({ acao: "registo", ...payload }),
    });
    setSession(data.token, data.utilizador);
    return data.utilizador;
  },

  logout: async () => {
    try {
      await request("/auth", {
        method: "POST",
        body: JSON.stringify({ acao: "logout" }),
      });
    } finally {
      clearSession();
    }
  },

  completarPerfil: (dados: Partial<Utilizador>) =>
    request<Utilizador>("/utilizadores/me", {
      method: "PATCH",
      body: JSON.stringify(dados),
    }),

  /* catálogo */
  safras: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<{ results?: Safra[] } | Safra[]>(`/safras${qs}`);
  },
  safra: (id: number | string) => request<Safra>(`/safras/${id}`),
  criarSafra: (form: FormData) =>
    request<Safra>("/safras", { method: "POST", body: form }),
  minhasSafras: (produtorId: number) =>
    request<{ results?: Safra[] } | Safra[]>(`/safras?produtor=${produtorId}`),
  produtos: () => request<{ results?: unknown[] } | unknown[]>("/produtos"),
  provincias: () => request<unknown[]>("/provincias"),

  /* compras / escrow */
  reservar: (safra_id: number, quantidade: string | number) =>
    request<Transacao>("/transacoes/reservar", {
      method: "POST",
      body: JSON.stringify({ safra_id, quantidade }),
    }),
  enviarComprovativo: (transacaoId: number, file: File) => {
    const form = new FormData();
    form.append("comprovativo", file);
    return request<Transacao>(`/transacoes/${transacaoId}/enviar-comprovativo`, {
      method: "POST",
      body: form,
    });
  },
  confirmarPagamento: (transacaoId: number) =>
    request<Transacao>(`/transacoes/${transacaoId}/confirmar-pagamento`, {
      method: "POST",
    }),
  enviarEncomenda: (transacaoId: number) =>
    request<Transacao>(`/transacoes/${transacaoId}/enviar`, { method: "POST" }),
  confirmarEntrega: (transacaoId: number) =>
    request<Transacao>(`/transacoes/${transacaoId}/confirmar-entrega`, {
      method: "POST",
    }),
  liquidar: (transacaoId: number) =>
    request<Transacao>(`/transacoes/${transacaoId}/liquidar`, { method: "POST" }),
  disputar: (transacaoId: number, motivo: string) =>
    request<Transacao>(`/transacoes/${transacaoId}/disputar`, {
      method: "POST",
      body: JSON.stringify({ motivo }),
    }),
  historicoTransacao: (transacaoId: number) =>
    request<unknown[]>(`/transacoes/${transacaoId}/historico`),

  /* transações do utilizador autenticado (o backend já filtra por partes) */
  transacoes: (filtro?: "compras" | "vendas") => {
    const u = getUsuario();
    if (filtro === "compras" && u)
      return request<{ results?: Transacao[] } | Transacao[]>(
        `/transacoes?comprador=${u.id}`
      );
    if (filtro === "vendas" && u)
      return request<{ results?: Transacao[] } | Transacao[]>(
        `/transacoes?vendedor=${u.id}`
      );
    return request<{ results?: Transacao[] } | Transacao[]>("/transacoes");
  },
};

/** Normaliza respostas DRF paginadas ({results}) ou listas simples. */
export function comoLista<T>(data: { results?: T[] } | T[]): T[] {
  return Array.isArray(data) ? data : data.results ?? [];
}
