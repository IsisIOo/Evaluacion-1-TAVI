<template>
  <v-container class="fill-height">
    <v-row justify="center">
      <v-col cols="12" sm="8" md="5">
        <v-card class="pa-6">
          <v-card-title class="text-h5 text-center mb-4">Crear Cuenta</v-card-title>

          <v-alert v-if="error" type="error" variant="tonal" closable class="mb-4" @click:close="error = ''">
            {{ error }}
          </v-alert>
          <v-alert v-if="success" type="success" variant="tonal" closable class="mb-4" @click:close="success = ''">
            {{ success }}
          </v-alert>

          <v-form ref="form" @submit.prevent="handleRegister">
            <v-text-field
              v-model="nombre"
              label="Nombre completo"
              :rules="[rules.required]"
              variant="outlined"
              prepend-inner-icon="mdi-account"
              class="mb-3"
            />

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
              :rules="[rules.required, rules.minLength]"
              variant="outlined"
              prepend-inner-icon="mdi-lock"
              class="mb-4"
            />

            <v-btn type="submit" color="primary" block size="large" :loading="loading">
              Registrarse
            </v-btn>
          </v-form>

          <v-divider class="my-4" />

          <p class="text-center text-body-2">
            ¿Ya tienes cuenta?
            <router-link to="/login">Inicia sesión aquí</router-link>
          </p>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import authService from "@/services/auth.service.js";

export default {
  name: "RegisterView",
  data: () => ({
    nombre: "",
    email: "",
    password: "",
    loading: false,
    error: "",
    success: "",
    rules: {
      required: (v) => !!v || "Este campo es obligatorio.",
      email: (v) => /.+@.+\..+/.test(v) || "Correo electrónico no válido.",
      minLength: (v) => (v && v.length >= 6) || "Mínimo 6 caracteres.",
    },
  }),
  methods: {
    async handleRegister() {
      const { valid } = await this.$refs.form.validate();
      if (!valid) return;

      this.loading = true;
      this.error = "";
      this.success = "";
      try {
        await authService.register({
          nombre: this.nombre,
          email: this.email,
          password: this.password,
        });
        this.success = "Cuenta creada exitosamente. Redirigiendo al login...";
        setTimeout(() => this.$router.push("/login"), 2000);
      } catch (err) {
        this.error = err.response?.data?.detail || "Error al registrarse.";
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>
