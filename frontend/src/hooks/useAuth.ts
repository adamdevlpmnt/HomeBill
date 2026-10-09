import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../lib/api";

interface AuthStatus {
  authenticated: boolean;
  app_name: string;
  currency_code: string;
  currency_symbol: string;
}

export function useAuth() {
  const queryClient = useQueryClient();

  const { data: status, isLoading } = useQuery<AuthStatus>({
    queryKey: ["auth_status"],
    queryFn: () => apiFetch<AuthStatus>("/api/auth/status"),
    staleTime: 1000 * 60 * 5, // 5 min
    retry: false,
  });

  const loginMutation = useMutation({
    mutationFn: (password: string) =>
      apiFetch<{ success: boolean; token: string }>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ password }),
      }),
    onSuccess: (data) => {
      if (data?.token) {
        localStorage.setItem("conso_token", data.token);
      }
      queryClient.setQueryData(["auth_status"], {
        authenticated: true,
        app_name: "Conso Maison",
        currency_code: "DZD",
        currency_symbol: "DA",
      });
      queryClient.invalidateQueries(); // Recharge les données
    },
  });

  const logoutMutation = useMutation({
    mutationFn: () =>
      apiFetch<{ success: boolean }>("/api/auth/logout", {
        method: "POST",
      }),
    onSuccess: () => {
      localStorage.removeItem("conso_token");
      queryClient.setQueryData(["auth_status"], {
        authenticated: false,
        app_name: "Conso Maison",
        currency_code: "DZD",
        currency_symbol: "DA",
      });
      queryClient.clear();
    },
  });

  return {
    isAuthenticated: !!status?.authenticated,
    isLoading,
    login: loginMutation.mutateAsync,
    logout: logoutMutation.mutateAsync,
    isLoggingIn: loginMutation.isPending,
  };
}
