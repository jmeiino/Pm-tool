import { create } from "zustand";

interface AuthUser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
  is_active: boolean;
  timezone: string;
  daily_capacity_hours: number;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;

  login: (access: string, refresh: string, user: AuthUser) => void;
  logout: () => void;
  setTokens: (access: string, refresh: string) => void;
}

function loadFromStorage(): Pick<AuthState, "accessToken" | "refreshToken" | "user" | "isAuthenticated"> {
  if (typeof window === "undefined") {
    return { accessToken: null, refreshToken: null, user: null, isAuthenticated: false };
  }
  const accessToken = localStorage.getItem("access_token");
  const refreshToken = localStorage.getItem("refresh_token");
  const userStr = localStorage.getItem("auth_user");
  const user = userStr ? JSON.parse(userStr) : null;
  return {
    accessToken,
    refreshToken,
    user,
    isAuthenticated: !!accessToken,
  };
}

export const useAuthStore = create<AuthState>((set) => ({
  ...loadFromStorage(),

  login: (access, refresh, user) => {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
    localStorage.setItem("auth_user", JSON.stringify(user));
    set({ accessToken: access, refreshToken: refresh, user, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("auth_user");
    set({ accessToken: null, refreshToken: null, user: null, isAuthenticated: false });
  },

  setTokens: (access, refresh) => {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
    set({ accessToken: access, refreshToken: refresh });
  },
}));
