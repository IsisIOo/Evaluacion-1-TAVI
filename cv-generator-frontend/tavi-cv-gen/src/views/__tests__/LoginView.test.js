import { describe, it, expect, beforeEach, vi } from "vitest";
import { shallowMount } from "@vue/test-utils";
import LoginView from "@/views/LoginView.vue";

vi.mock("@/services/auth.service", () => ({
  default: { login: vi.fn() },
}));

import authService from "@/services/auth.service";

const validFormStub = {
  name: "VFormStub",
  template: "<div><slot /></div>",
  methods: { validate: async () => ({ valid: true }) },
};

const makeWrapper = (push, formStub = validFormStub) =>
  shallowMount(LoginView, {
    global: {
      stubs: { "v-form": formStub, "router-link": true },
      mocks: { $router: { push } },
    },
  });

describe("LoginView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("llama a authService.login y navega a / cuando todo es válido", async () => {
    authService.login.mockResolvedValue({ access_token: "abc" });
    const push = vi.fn();
    const wrapper = makeWrapper(push);

    wrapper.vm.email = "test@example.com";
    wrapper.vm.password = "secret";
    await wrapper.vm.handleLogin();

    expect(authService.login).toHaveBeenCalledWith({
      email: "test@example.com",
      password: "secret",
    });
    expect(push).toHaveBeenCalledWith("/");
    expect(wrapper.vm.loading).toBe(false);
  });

  it("muestra el detail del backend cuando el login falla", async () => {
    authService.login.mockRejectedValue({
      response: { data: { detail: "Credenciales inválidas" } },
    });
    const wrapper = makeWrapper(vi.fn());

    wrapper.vm.email = "test@example.com";
    wrapper.vm.password = "incorrecta";
    await wrapper.vm.handleLogin();

    expect(wrapper.vm.error).toBe("Credenciales inválidas");
    expect(wrapper.vm.loading).toBe(false);
  });

  it("usa mensaje por defecto si el error no trae detail", async () => {
    authService.login.mockRejectedValue(new Error("Network Error"));
    const wrapper = makeWrapper(vi.fn());

    wrapper.vm.email = "test@example.com";
    wrapper.vm.password = "secret";
    await wrapper.vm.handleLogin();

    expect(wrapper.vm.error).toBe("Error al iniciar sesión.");
  });

  it("no llama al servicio ni navega si la validación del formulario falla", async () => {
    const invalidFormStub = {
      template: "<div><slot /></div>",
      methods: { validate: async () => ({ valid: false }) },
    };
    const push = vi.fn();
    const wrapper = makeWrapper(push, invalidFormStub);

    await wrapper.vm.handleLogin();

    expect(authService.login).not.toHaveBeenCalled();
    expect(push).not.toHaveBeenCalled();
  });
});
