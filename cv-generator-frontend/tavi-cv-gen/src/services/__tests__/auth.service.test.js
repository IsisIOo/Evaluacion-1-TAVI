import { describe, it, expect, beforeEach, vi } from "vitest";
import authService from "@/services/auth.service";

vi.mock("@/http-common", () => ({
  default: { post: vi.fn() },
}));

import httpClient from "@/http-common";

const makeToken = (sub) => {
  const payload = btoa(JSON.stringify({ sub, iat: 1 }))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
  return `header.${payload}.signature`;
};

describe("auth.service login", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("envía el login como form-urlencoded", async () => {
    httpClient.post.mockResolvedValue({
      data: { access_token: makeToken("user-1"), token_type: "bearer" },
    });

    await authService.login({ email: "test@example.com", password: "secret" });

    const [url, params, config] = httpClient.post.mock.calls[0];
    expect(url).toBe("/api/auth/login");
    expect(params).toBeInstanceOf(URLSearchParams);
    expect(params.get("username")).toBe("test@example.com");
    expect(params.get("password")).toBe("secret");
    expect(config.headers["Content-Type"]).toBe("application/x-www-form-urlencoded");
  });

  it("guarda token y usuario en localStorage al recibir access_token", async () => {
    const token = makeToken("user-123");
    httpClient.post.mockResolvedValue({
      data: { access_token: token, token_type: "bearer" },
    });

    const result = await authService.login({
      email: "test@example.com",
      password: "secret",
    });

    expect(localStorage.getItem("token")).toBe(token);
    const user = JSON.parse(localStorage.getItem("user"));
    expect(user.id).toBe("user-123");
    expect(user.email).toBe("test@example.com");
    expect(result.token_type).toBe("bearer");
  });

  it("no toca localStorage si la respuesta no trae token", async () => {
    httpClient.post.mockResolvedValue({ data: {} });

    await authService.login({ email: "test@example.com", password: "secret" });

    expect(localStorage.getItem("token")).toBeNull();
    expect(localStorage.getItem("user")).toBeNull();
  });
});

describe("auth.service register", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("hace POST /register con el DTO", async () => {
    const dto = { email: "nuevo@example.com", password: "123456" };
    httpClient.post.mockResolvedValue({ data: { id: "user-1", email: dto.email } });

    const result = await authService.register(dto);

    expect(httpClient.post).toHaveBeenCalledWith("/api/auth/register", dto);
    expect(result.email).toBe("nuevo@example.com");
  });
});

describe("auth.service sesión", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("logout limpia token y usuario", () => {
    localStorage.setItem("token", "abc");
    localStorage.setItem("user", JSON.stringify({ id: "user-1" }));

    authService.logout();

    expect(localStorage.getItem("token")).toBeNull();
    expect(localStorage.getItem("user")).toBeNull();
  });

  it("getCurrentUser devuelve el usuario parseado o null", () => {
    expect(authService.getCurrentUser()).toBeNull();
    localStorage.setItem("user", JSON.stringify({ id: "user-1", email: "a@b.c" }));
    expect(authService.getCurrentUser()).toEqual({ id: "user-1", email: "a@b.c" });
  });

  it("getToken devuelve el token guardado", () => {
    expect(authService.getToken()).toBeNull();
    localStorage.setItem("token", "mi-token");
    expect(authService.getToken()).toBe("mi-token");
  });

  it("isLoggedIn refleja la existencia del token", () => {
    expect(authService.isLoggedIn()).toBe(false);
    localStorage.setItem("token", "mi-token");
    expect(authService.isLoggedIn()).toBe(true);
  });
});
