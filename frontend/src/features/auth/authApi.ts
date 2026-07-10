import { useMutation } from "@tanstack/react-query";

import { api } from "@/app/apiClient";

interface ForgotPasswordResponse {
  sent: boolean;
  message: string;
}

interface ResetPasswordResponse {
  ok: boolean;
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: async (vars: { email: string }) => {
      const { data } = await api.post<ForgotPasswordResponse>("/auth/forgot-password", {
        email: vars.email,
      });
      return data;
    },
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: async (vars: { token: string; newPassword: string }) => {
      const { data } = await api.post<ResetPasswordResponse>("/auth/reset-password", {
        token: vars.token,
        new_password: vars.newPassword,
      });
      return data;
    },
  });
}
