<template>
  <v-container class="fill-height">
    <v-row justify="center">
      <v-col cols="12" sm="8" md="5">
        <v-card class="pa-6">
          <v-card-title class="text-h5 text-center mb-4">Iniciar Sesión</v-card-title>

          <v-alert v-if="error" type="error" variant="tonal" closable class="mb-4" @click:close="error = ''">
            {{ error }}
          </v-alert>

          <v-form ref="form" @submit.prevent="handleLogin">
            <v-text-field
              v-model="email"
              label="Correo electrónico"
              type="email"
              :rules="[rules.required, rules.email]"
              variant="outlined"
              prepend-inner-icon="mdi-email"
              class="mb-3"
            />

            <v-text-field
              v-model="password"
              label="Contraseña"
              type="password"
              :rules="[rules.required]"
              variant="outlined"
              prepend-inner-icon="mdi-lock"
              class="mb-4"
            />

            <v-btn type="submit" color="primary" block size="large" :loading="loading">
              Ingresar
            </v-btn>
          </v-form>

          <v-divider class="my-4" />

          <p class="text-center text-body-2">
            ¿No tienes cuenta?
            <router-link to="/register">Regístrate aquí</router-link>
          </p>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import authService from "@/services/auth.service.js";

export default {
  name: "LoginView",
  data: () => ({
    email: "",
    password: "",
    loading: false,
    error: "",
    rules: {
      required: (v) => !!v || "Este campo es obligatorio.",
      email: (v) => /.+@.+\..+/.test(v) || "Correo electrónico no válido.",
    },
  }),
  methods: {
    async handleLogin() {
      const { valid } = await this.$refs.form.validate();
      if (!valid) return;

      this.loading = true;
      this.error = "";
      try {
        await authService.login({ email: this.email, password: this.password });
        this.$router.push("/");
      } catch (err) {
        this.error = err.response?.data?.detail || "Error al iniciar sesión.";
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>
