<template>
  <v-container class="py-10">
    <v-row justify="center">
      <v-col cols="12" md="10" lg="8">
        <h2 class="text-h4 mb-6 text-center">Mis CVs Generados</h2>

        <v-alert v-if="error" type="error" variant="tonal" closable class="mb-4" @click:close="error = ''">
          {{ error }}
        </v-alert>

        <div v-if="loading" class="text-center py-10">
          <v-progress-circular indeterminate color="primary" />
          <p class="mt-2">Cargando CVs...</p>
        </div>

        <div v-else-if="cvs.length === 0" class="text-center py-10">
          <v-icon icon="mdi-file-document-outline" size="64" color="grey-lighten-1" />
          <p class="text-h6 text-grey mt-4">No has generado ningún CV todavía.</p>
          <v-btn color="primary" to="/form" class="mt-4">Generar mi primer CV</v-btn>
        </div>

        <v-list v-else lines="three">
          <v-list-item v-for="cv in cvs" :key="cv._id" class="mb-2 border rounded" @click="viewCv(cv._id)">
            <template v-slot:prepend>
              <v-icon icon="mdi-file-document" color="primary" />
            </template>

            <v-list-item-title class="font-weight-bold">
              {{ cv.personal?.nombre_completo || 'CV sin nombre' }}
            </v-list-item-title>

            <v-list-item-subtitle>
              {{ cv.personal?.profesion || '' }}
            </v-list-item-subtitle>

            <v-list-item-subtitle v-if="cv.remaining_days !== undefined" class="mt-1">
              <v-icon size="small" :color="expirationColor(cv.remaining_days)" class="mr-1">
                mdi-clock-outline
              </v-icon>
              {{ expirationLabel(cv.remaining_days) }}
              <span v-if="cv.expires_at" class="text-caption text-grey">— {{ formatExpiration(cv.expires_at) }}</span>
            </v-list-item-subtitle>

            <template v-slot:append>
              <v-chip v-if="cv.remaining_days !== undefined" size="small" :color="expirationColor(cv.remaining_days)">
                {{ expirationChip(cv.remaining_days) }}
              </v-chip>
              <v-btn icon="mdi-chevron-right" variant="text" />
            </template>
          </v-list-item>
        </v-list>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import httpClient from "@/http-common.js";
import authService from "@/services/auth.service.js";

export default {
  name: "MyCvsView",
  data: () => ({
    cvs: [],
    loading: true,
    error: "",
  }),
  async mounted() {
    const user = authService.getCurrentUser();
    if (!user) {
      this.$router.push("/login");
      return;
    }
    try {
      const res = await httpClient.get(`/api/cv/user/${user.id}`);
      this.cvs = res.data.cvs || [];
    } catch (err) {
      this.error = err.userMessage || "Error al cargar los CVs.";
    } finally {
      this.loading = false;
    }
  },
  methods: {
    viewCv(cvId) {
      this.$router.push({ name: "pdf", params: { cvId } });
    },
    formatExpiration(iso) {
      if (!iso) return "";
      const date = new Date(iso);
      return date.toLocaleDateString("es-CL");
    },
    expirationLabel(days) {
      if (days <= 0) return "Vence hoy";
      return `Expira en ${days} día${days === 1 ? "" : "s"}`;
    },
    expirationChip(days) {
      if (days <= 0) return "Vencido";
      return `${days}d`;
    },
    expirationColor(days) {
      if (days <= 0) return "error";
      if (days <= 3) return "error";
      if (days <= 7) return "warning";
      return "success";
    },
  },
};
</script>
