<template>
  <v-container class="fill-height">
    <v-responsive class="align-center text-center fill-height">
      <!-- Encabezado Principal -->
      <v-img
        height="225"
        src="@/assets/danbo.png" 
        class="mb-4"
      />
      <div class="text-overline mb-2">Proyecto TAVI - USACH</div>
      
      <h1 class="text-h2 font-weight-bold mb-3">
        Generador de CV con IA
      </h1>

      <p class="text-h6 font-weight-light mb-10 text-grey-darken-1">
        Optimiza tu perfil profesional para el formato estándar de la universidad 
        utilizando inteligencia artificial avanzada.
      </p>

      <v-row class="d-flex align-center justify-center mb-10">
        <v-col cols="12" md="4">
          <v-card variant="flat" class="py-4">
            <v-icon size="x-large" color="primary" icon="mdi-form-select" />
            <v-card-text>Responde preguntas clave sobre tu perfil</v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" md="4">
          <v-card variant="flat" class="py-4">
            <v-icon size="x-large" color="primary" icon="mdi-robot-outline" />
            <v-card-text>Nuestra IA optimiza tus textos y logros</v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" md="4">
          <v-card variant="flat" class="py-4">
            <v-icon size="x-large" color="primary" icon="mdi-file-pdf-box" />
            <v-card-text>Descarga tu CV en formato PDF listo para postular</v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <v-btn
        color="primary"
        size="x-large"
        variant="elevated"
        elevation="4"
        rounded="lg"
        class="px-10"
        @click="startForm"
      >
        Empecemos
        <v-icon end icon="mdi-chevron-right" />
      </v-btn>
    </v-responsive>
  </v-container>
</template>

<script>
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'HomeView',

  methods: {
    startForm() {
      // Por ahora solo haremos un log, luego lo conectaremos al router
      console.log('Navegando al formulario...');
      this.$router.push('/form'); 
    },
  },
});
</script>

<style scoped>
/* Puedes añadir ajustes finos aquí si lo necesitas */
.v-card {
  transition: transform 0.2s;
}
.v-card:hover {
  transform: translateY(-5px);
}
</style>