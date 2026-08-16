import { describe, it, expect, beforeEach, vi } from "vitest";
import { shallowMount } from "@vue/test-utils";
import RegisterView from "@/views/RegisterView.vue";

vi.mock("@/services/auth.service", () => ({
  default: { register: vi.fn() },
}));

import authService from "@/services/auth.service";

const validFormStub = {
  name: "VFormStub",
  template: "<div><slot /></div>",
  methods: { validate: async () => ({ valid: true }) },
};

const makeWrapper = (push, formStub = validFormStub) =>
  shallowMount(RegisterView, {
    global: {
      stubs: { "v-form": formStub, "router-link": true },
      mocks: { $router: { push } },
    },
  });

describe("RegisterView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("llama a authService.register y muestra éxito cuando todo es válido", async () => {
    authService.register.mockResolvedValue({ id: "user-1" });
    const push = vi.fn();
    const wrapper = makeWrapper(push);

    wrapper.vm.nombre = "Juan Pérez";
    wrapper.vm.email = "juan@example.com";
    wrapper.vm.password = "secreto123";
    await wrapper.vm.handleRegister();

    expect(authService.register).toHaveBeenCalledWith({
      nombre: "Juan Pérez",
      email: "juan@example.com",
      password: "secreto123",
    });
    expect(wrapper.vm.success).toContain("Cuenta creada exitosamente");
    expect(wrapper.vm.loading).toBe(false);

    vi.advanceTimersByTime(2000);
    expect(push).toHaveBeenCalledWith("/login");
  });

  it("muestra el detail del backend cuando el registro falla", async () => {
    authService.register.mockRejectedValue({
      response: { data: { detail: "El correo ya está registrado" } },
    });
    const wrapper = makeWrapper(vi.fn());

    wrapper.vm.nombre = "Juan Pérez";
    wrapper.vm.email = "juan@example.com";
    wrapper.vm.password = "secreto123";
    await wrapper.vm.handleRegister();

    expect(wrapper.vm.error).toBe("El correo ya está registrado");
    expect(wrapper.vm.success).toBe("");
    expect(wrapper.vm.loading).toBe(false);
  });

  it("no llama al servicio si la validación del formulario falla", async () => {
    const invalidFormStub = {
      template: "<div><slot /></div>",
      methods: { validate: async () => ({ valid: false }) },
    };
    const wrapper = makeWrapper(vi.fn(), invalidFormStub);

    await wrapper.vm.handleRegister();

    expect(authService.register).not.toHaveBeenCalled();
    expect(wrapper.vm.success).toBe("");
  });
});
