import { describe, it, expect } from "vitest";
import { validateRut, formatRut, formatPhone, monthLabel, ciudadesCl, paises } from "@/views/FormView.vue";

describe("validateRut", () => {
  it("acepta un RUT chileno válido (11.111.111-1)", () => {
    expect(validateRut("11.111.111-1")).toBe(true);
    expect(validateRut("11111111-1")).toBe(true);
    expect(validateRut("111111111")).toBe(true);
  });

  it("acepta un RUT válido terminado en K", () => {
    expect(validateRut("16.803.475-K")).toBe(true);
  });

  it("rechaza un RUT con dígito verificador inválido", () => {
    expect(validateRut("11.111.111-2")).toBe(false);
  });

  it("rechaza valores vacíos o muy cortos", () => {
    expect(validateRut("")).toBe(false);
    expect(validateRut(null)).toBe(false);
    expect(validateRut(undefined)).toBe(false);
    expect(validateRut("1")).toBe(false);
  });

  it("rechaza RUTs con caracteres inválidos", () => {
    expect(validateRut("abcdefgh1")).toBe(false);
    expect(validateRut("11111111-X")).toBe(false);
  });
});

describe("formatRut", () => {
  it("formatea con puntos y guion", () => {
    expect(formatRut("11111111-1")).toBe("11.111.111-1");
    expect(formatRut("16700000-4")).toBe("16.700.000-4");
  });

  it("devuelve vacío sin valor", () => {
    expect(formatRut("")).toBe("");
    expect(formatRut(null)).toBe("");
  });
});

describe("formatPhone", () => {
  it("formatea un celular chileno de 9 dígitos", () => {
    expect(formatPhone("987654321")).toBe("+56 9 9876 54321");
    expect(formatPhone("+56987654321")).toBe("+56 9 8765 4321");
  });

  it("formatea un número con prefijo 56 (11 dígitos)", () => {
    expect(formatPhone("56987654321")).toBe("+56 9 8765 4321");
  });

  it("devuelve el valor original si no se reconoce", () => {
    expect(formatPhone("123456")).toBe("123456");
    expect(formatPhone("")).toBe("");
    expect(formatPhone(null)).toBe("");
  });
});

describe("monthLabel", () => {
  it("convierte YYYY-MM a nombre de mes en español", () => {
    expect(monthLabel("2024-01")).toBe("Enero 2024");
    expect(monthLabel("2023-12")).toBe("Diciembre 2023");
  });

  it("devuelve vacío para formatos inválidos", () => {
    expect(monthLabel("")).toBe("");
    expect(monthLabel("2024")).toBe("");
    expect(monthLabel("2024/01")).toBe("");
    expect(monthLabel(null)).toBe("");
  });
});

describe("listas estáticas", () => {
  it("incluye ciudades de Chile", () => {
    expect(ciudadesCl).toContain("Santiago");
    expect(ciudadesCl).toContain("Valparaíso");
  });

  it("incluye países de Latinoamérica", () => {
    expect(paises).toContain("Chile");
    expect(paises).toContain("Perú");
    expect(paises).toContain("España");
  });
});
