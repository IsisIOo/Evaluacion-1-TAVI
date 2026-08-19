import { describe, it, expect, beforeEach } from "vitest";
import httpClient from "@/http-common";

const responseHandlers = httpClient.interceptors.response.handlers;
const requestHandlers = httpClient.interceptors.request.handlers;
const onResponseFulfilled = responseHandlers[0].fulfilled;
const onResponseRejected = responseHandlers[0].rejected;
const onRequestFulfilled = requestHandlers[0].fulfilled;

describe("http-common interceptor de respuesta", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("pasa las respuestas exitosas sin cambios", () => {
    const response = { data: { success: true } };
    expect(onResponseFulfilled(response)).toBe(response);
  });

  it("marca mensaje de timeout por ECONNABORTED", async () => {
    const error = { code: "ECONNABORTED" };
    await expect(onResponseRejected(error)).rejects.toBe(error);
    expect(error.userMessage).toContain("tardando demasiado");
  });

  it("marca mensaje de timeout si el mensaje lo indica", async () => {
    const error = { message: "timeout of 30000ms exceeded" };
    await expect(onResponseRejected(error)).rejects.toBe(error);
    expect(error.userMessage).toContain("tardando demasiado");
  });

  it("marca servidor caído cuando no hay respuesta", async () => {
    const error = { message: "Network Error" };
    await expect(onResponseRejected(error)).rejects.toBe(error);
    expect(error.userMessage).toContain("servidor está caído");
  });

  it("usa el detail del backend para el 429", async () => {
    const error = { response: { status: 429, data: { detail: "Cuota agotada" } } };
    await expect(onResponseRejected(error)).rejects.toBe(error);
    expect(error.userMessage).toBe("Cuota agotada");
  });

  it("usa mensaje por defecto para 429 sin detail", async () => {
    const error = { response: { status: 429, data: {} } };
    await expect(onResponseRejected(error)).rejects.toBe(error);
    expect(error.userMessage).toContain("cuota de la API");
  });

  it("marca mensaje de IA lenta para 504", async () => {
    const error = { response: { status: 504, data: {} } };
    await expect(onResponseRejected(error)).rejects.toBe(error);
    expect(error.userMessage).toContain("IA generadora");
  });

  it("usa el detail del backend para errores 5xx", async () => {
    const error = { response: { status: 500, data: { detail: "Error interno controlado" } } };
    await expect(onResponseRejected(error)).rejects.toBe(error);
    expect(error.userMessage).toBe("Error interno controlado");
  });

  it("marca mensaje por defecto para 500 sin detail", async () => {
    const error = { response: { status: 500, data: {} } };
    await expect(onResponseRejected(error)).rejects.toBe(error);
    expect(error.userMessage).toContain("interno del servidor");
  });

  it("marca recurso no encontrado para 404", async () => {
    const error = { response: { status: 404, data: {} } };
    await expect(onResponseRejected(error)).rejects.toBe(error);
    expect(error.userMessage).toContain("no se encontró");
  });

  it("usa el detail del backend para otros códigos", async () => {
    const error = { response: { status: 422, data: { detail: "Datos inválidos" } } };
    await expect(onResponseRejected(error)).rejects.toBe(error);
    expect(error.userMessage).toBe("Datos inválidos");
  });

  it("marca error inesperado si no hay detail", async () => {
    const error = { response: { status: 400, data: {} } };
    await expect(onResponseRejected(error)).rejects.toBe(error);
    expect(error.userMessage).toContain("error inesperado");
  });
});

describe("http-common interceptor de request", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("agrega el header Authorization si hay token", () => {
    localStorage.setItem("token", "mi-token");
    const config = { headers: {} };
    const result = onRequestFulfilled(config);
    expect(result.headers.Authorization).toBe("Bearer mi-token");
  });

  it("no agrega Authorization si no hay token", () => {
    const config = { headers: {} };
    const result = onRequestFulfilled(config);
    expect(result.headers.Authorization).toBeUndefined();
  });
});
