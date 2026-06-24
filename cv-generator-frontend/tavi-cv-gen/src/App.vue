<template>
  <v-app>
    <v-app-bar flat color="primary" density="compact">
      <v-app-bar-title>
        <router-link to="/" class="text-white text-decoration-none">CV Generator</router-link>
      </v-app-bar-title>

      <template v-slot:append>
        <v-btn to="/form" variant="text" class="text-white">Generar CV</v-btn>

        <template v-if="isLoggedIn">
          <v-btn to="/my-cvs" variant="text" class="text-white">Mis CVs</v-btn>
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-btn v-bind="props" variant="text" class="text-white" prepend-icon="mdi-account">
                {{ user?.email }}
              </v-btn>
            </template>
            <v-list>
              <v-list-item @click="logout">
                <v-list-item-title>Cerrar sesión</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </template>

        <template v-else>
          <v-btn to="/login" variant="text" class="text-white">Iniciar sesión</v-btn>
          <v-btn to="/register" variant="outlined" class="text-white border-white">Registrarse</v-btn>
        </template>
      </template>
    </v-app-bar>

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script>
import authService from "@/services/auth.service.js";

export default {
  name: "App",
  data: () => ({
    isLoggedIn: authService.isLoggedIn(),
    user: authService.getCurrentUser(),
  }),
  methods: {
    logout() {
      authService.logout();
      this.isLoggedIn = false;
      this.user = null;
      this.$router.push("/");
    },
  },
  created() {
    this.$router.afterEach(() => {
      this.isLoggedIn = authService.isLoggedIn();
      this.user = authService.getCurrentUser();
    });
  },
};
</script>
