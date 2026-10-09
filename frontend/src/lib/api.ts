// Client API HTTP avec fetch natif, cookies HttpOnly et header Authorization Bearer

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.status = status;
    this.data = data;
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = endpoint.startsWith("http") ? endpoint : endpoint;
  const headers = new Headers(options.headers || {});

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  // Token de secours si le cookie HttpOnly est bloqué sur localhost multi-port
  const token = localStorage.getItem("conso_token");
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "include", // Envoie automatiquement le cookie HttpOnly
  });

  if (response.status === 204) {
    return {} as T;
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const errorMsg = data?.detail || `Erreur ${response.status} : ${response.statusText}`;
    throw new ApiError(response.status, errorMsg, data);
  }

  return data as T;
}
