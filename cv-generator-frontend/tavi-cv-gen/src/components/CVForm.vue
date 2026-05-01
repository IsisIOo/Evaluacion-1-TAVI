<template>
  <v-container class="py-8">
    <v-row>
      <v-col cols="12" md="8" offset-md="2">
        <v-card class="pa-6">
          <v-card-title class="text-h4 mb-6">Generador de CV con IA</v-card-title>
          
          <v-form @submit.prevent="generateCV">
            <!-- Información Personal -->
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="form.full_name"
                  label="Nombre Completo"
                  required
                />
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="form.email"
                  label="Email"
                  type="email"
                  required
                />
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="form.phone"
                  label="Teléfono"
                />
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="form.professional_title"
                  label="Título Profesional"
                />
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="form.location"
                  label="Ubicación"
                />
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="form.linkedin"
                  label="LinkedIn"
                />
              </v-col>
            </v-row>

            <!-- Resumen Profesional -->
            <v-text-field
              v-model="form.summary"
              label="Resumen Profesional"
              type="textarea"
              rows="3"
              class="mb-4"
            />

            <!-- Habilidades Técnicas -->
            <v-text-field
              v-model="skillsInput"
              label="Habilidades Técnicas (separadas por comas)"
              hint="Ej: Python, FastAPI, Docker"
              class="mb-4"
              @blur="parseSkills"
            />

            <!-- Botón Generar -->
            <v-row>
              <v-col cols="12">
                <v-btn
                  type="submit"
                  color="primary"
                  size="large"
                  class="w-100"
                  :loading="loading"
                  :disabled="loading"
                >
                  Generar CV
                </v-btn>
              </v-col>
            </v-row>
          </v-form>

          <!-- Mensajes de Estado -->
          <v-alert
            v-if="error"
            type="error"
            class="mt-4"
            closable
          >
            {{ error }}
          </v-alert>

          <v-alert
            v-if="successMessage"
            type="success"
            class="mt-4"
            closable
          >
            {{ successMessage }}
          </v-alert>
        </v-card>

        <!-- Resultado del CV -->
        <v-card v-if="cvResult" class="mt-6 pa-6">
          <v-card-title class="text-h5 mb-4">CV Generado</v-card-title>
          <v-divider class="mb-4"></v-divider>

          <div class="cv-output">
            <pre class="bg-grey-lighten-3 pa-4 rounded">{{ JSON.stringify(cvResult, null, 2) }}</pre>
          </div>

          <v-row class="mt-4">
            <v-col cols="12">
              <v-btn
                color="primary"
                @click="downloadJSON"
                class="mr-2"
              >
                Descargar JSON
              </v-btn>
              <v-btn
                color="secondary"
                @click="copyToClipboard"
              >
                Copiar al Portapapeles
              </v-btn>
            </v-col>
          </v-row>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { defineComponent } from 'vue';
import ClienteService from '../services/cliente.service';

export default defineComponent({
  name: 'CVForm',
  
  data() {
    return {
      form: {
        full_name: '',
        email: '',
        phone: '',
        professional_title: '',
        location: '',
        linkedin: '',
        summary: '',
        technical_skills: [],
      },
      skillsInput: '',
      loading: false,
      error: '',
      successMessage: '',
      cvResult: null,
    };
  },

  methods: {
    parseSkills() {
      if (this.skillsInput) {
        this.form.technical_skills = this.skillsInput
          .split(',')
          .map(skill => skill.trim())
          .filter(skill => skill);
      }
    },

    async generateCV() {
      this.error = '';
      this.successMessage = '';
      
      if (!this.form.full_name || !this.form.email) {
        this.error = 'Por favor completa al menos Nombre y Email';
        return;
      }

      this.loading = true;
      try {
        const response = await ClienteService.generateCV(this.form);
        this.cvResult = response.data.cv;
        this.successMessage = 'CV generado exitosamente con ' + response.data.model;
      } catch (err) {
        this.error = err.response?.data?.detail || 'Error al generar el CV. Intenta de nuevo.';
        console.error('Error:', err);
      } finally {
        this.loading = false;
      }
    },

    downloadJSON() {
      const dataStr = JSON.stringify(this.cvResult, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `CV_${this.form.full_name.replace(/\s+/g, '_')}.json`;
      link.click();
      URL.revokeObjectURL(url);
    },

    copyToClipboard() {
      const text = JSON.stringify(this.cvResult, null, 2);
      navigator.clipboard.writeText(text).then(() => {
        this.successMessage = 'Copiado al portapapeles';
      });
    },
  },
});
</script>

<style scoped>
.cv-output {
  max-height: 500px;
  overflow-y: auto;
}

pre {
  font-size: 12px;
  line-height: 1.4;
}

.w-100 {
  width: 100%;
}
</style>
