<template>
  <v-container class="py-10">
    <v-row justify="center">
      <v-col cols="12" md="10" lg="8">
        <h2 class="text-h4 mb-6 text-center">Formulario de Generación de CV</h2>
        
        <v-stepper v-model="step">
          <v-stepper-header>
            <template v-for="n in steps.length" :key="n">
              <v-stepper-item :title="steps[n-1]" :value="n" :complete="step > n"></v-stepper-item>
              <v-divider v-if="n !== steps.length"></v-divider>
            </template>
          </v-stepper-header>

          <v-stepper-window>
            <!-- Paso 1: Contacto -->
            <v-stepper-window-item :value="1">
              <v-form ref="formStep1">
                <v-card title="Información Personal" flat class="pa-4">
                  <v-row>
                    <v-col cols="12" md="6">
                      <v-text-field v-model="form.personal.nombre_completo" label="Nombre Completo *" :rules="[rules.required]" variant="outlined" />
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field v-model="form.personal.profesion" label="Profesión / Cargo *" :rules="[rules.required]" variant="outlined" />
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field v-model="form.personal.rut" label="RUT *" :rules="[rules.required]" variant="outlined" placeholder="12.345.678-K" />
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field v-model="form.personal.ciudad" label="Ciudad *" :rules="[rules.required]" variant="outlined" />
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field v-model="form.personal.email" label="Correo Electrónico *" :rules="[rules.required, rules.email]" variant="outlined" />
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field v-model="form.personal.telefono" label="Teléfono *" :rules="[rules.required]" variant="outlined" />
                    </v-col>
                    <v-col cols="12">
                      <v-text-field v-model="form.personal.linkedin" label="URL LinkedIn (Opcional)" variant="outlined" hint="Ej: https://linkedin.com/in/usuario" persistent-hint />
                    </v-col>
                  </v-row>
                </v-card>
              </v-form>
            </v-stepper-window-item>

            <!-- Paso 2: Perfil y Habilidades -->
            <v-stepper-window-item :value="2">
              <v-form ref="formStep2">
                <v-card title="Perfil Profesional y Habilidades" flat class="pa-4">
                  <v-slider v-model="form.perfil.anios_experiencia" label="Años de experiencia" min="0" max="40" step="1" thumb-label color="primary" />
                  
                  <v-textarea v-model="form.perfil.experticia" label="Tus áreas de experticia *" :rules="[rules.required]" variant="outlined" rows="3" />
                  
                  <v-textarea v-model="form.perfil.propuesta_valor" label="Tu propuesta de valor *" :rules="[rules.required]" variant="outlined" rows="3">
                    <template v-slot:append>
                      <v-tooltip location="top" text="Enfócate en el área o trabajo que tienes en la mira.">
                        <template v-slot:activator="{ props }">
                          <v-icon v-bind="props" icon="mdi-help-circle-outline" color="primary" />
                        </template>
                      </v-tooltip>
                    </template>
                  </v-textarea>

                  <v-textarea v-model="form.habilidades" label="Habilidades Técnicas e Idiomas *" :rules="[rules.required]" variant="outlined" rows="3" placeholder="Ej: Python (Avanzado), Inglés (B2), Excel (Intermedio)">
                    <template v-slot:append>
                      <v-tooltip location="top" text="Indica el software o idioma seguido de tu nivel de dominio para que la IA lo organice.">
                        <template v-slot:activator="{ props }">
                          <v-icon v-bind="props" icon="mdi-help-circle-outline" color="primary" />
                        </template>
                      </v-tooltip>
                    </template>
                  </v-textarea>
                </v-card>
              </v-form>
            </v-stepper-window-item>

            <!-- Paso 3: Experiencia -->
            <v-stepper-window-item :value="3">
              <v-form ref="formStep3">
                <v-card title="Trayectoria Profesional" flat class="pa-4">
                  <div v-for="(exp, index) in form.experiencias" :key="index" class="mb-6 pa-4 border rounded">
                    <div class="d-flex justify-space-between align-center mb-2">
                      <span class="text-subtitle-1 font-weight-bold">Experiencia #{{ index + 1 }}</span>
                      <v-btn icon="mdi-delete" size="small" color="error" variant="text" @click="removeExp(index)" v-if="form.experiencias.length > 1" />
                    </div>
                    <v-row>
                      <v-col cols="12" md="6"><v-text-field v-model="exp.cargo" label="Cargo *" :rules="[rules.required]" variant="outlined" /></v-col>
                      <v-col cols="12" md="6"><v-text-field v-model="exp.empresa" label="Empresa *" :rules="[rules.required]" variant="outlined" /></v-col>
                      <v-col cols="12" md="6"><v-text-field v-model="exp.periodo" label="Periodo (Inicio - Fin) *" placeholder="Marzo 2024 - Actualidad" :rules="[rules.required]" variant="outlined" /></v-col>
                      <v-col cols="12" md="6"><v-text-field v-model="exp.pais" label="País *" :rules="[rules.required]" variant="outlined" /></v-col>
                      <v-col cols="12"><v-textarea v-model="exp.descripcion" label="Descripción y Logros *" :rules="[rules.required]" variant="outlined" rows="2" hint="Describe tus tareas y menciona al menos un logro." persistent-hint /></v-col>
                    </v-row>
                  </div>
                  <v-btn prepend-icon="mdi-plus" variant="tonal" color="primary" @click="addExp">Agregar otra experiencia</v-btn>
                </v-card>
              </v-form>
            </v-stepper-window-item>

            <!-- Paso 4: Formación -->
            <v-stepper-window-item :value="4">
              <v-form ref="formStep4">
                <v-card title="Formación Educativa" flat class="pa-4">
                  <div v-for="(edu, index) in form.formacion" :key="index" class="mb-6 pa-4 border rounded">
                    <div class="d-flex justify-space-between align-center mb-2">
                      <span class="text-subtitle-1 font-weight-bold">Educación #{{ index + 1 }}</span>
                      <v-btn icon="mdi-delete" size="small" color="error" variant="text" @click="removeEdu(index)" v-if="form.formacion.length > 1" />
                    </div>
                    <v-row>
                      <v-col cols="12" md="6"><v-text-field v-model="edu.titulo" label="Título / Diploma *" :rules="[rules.required]" variant="outlined" /></v-col>
                      <v-col cols="12" md="6"><v-text-field v-model="edu.institucion" label="Institución *" :rules="[rules.required]" variant="outlined" /></v-col>
                      <v-col cols="12"><v-text-field v-model="edu.periodo" label="Periodo (Inicio - Fin) *" placeholder="2020 - 2026" :rules="[rules.required]" variant="outlined" /></v-col>
                    </v-row>
                  </div>
                  <v-btn prepend-icon="mdi-plus" variant="tonal" color="primary" @click="addEdu">Agregar otra formación</v-btn>
                </v-card>
              </v-form>
            </v-stepper-window-item>

            <!-- Paso 5: Finalizar -->
            <v-stepper-window-item :value="5">
              <v-card title="Finalizar y Enviar" flat class="pa-4">
                <p class="mb-4">Revisa tus datos antes de enviar a la IA.</p>
                <v-checkbox v-model="valid" label="Confirmo que la información es correcta" :rules="[v => !!v || 'Debes confirmar para continuar']" color="primary" />
              </v-card>
            </v-stepper-window-item>
          </v-stepper-window>

          <!-- Alerta de Error de validación -->
          <v-alert  
            v-if="showValidationError"  
            type="error"  
            variant="tonal"  
            class="mx-4 mb-2"  
            density="compact" 
            closable 
            @click:close="showValidationError = false" 
          >
            Debe rellenar todos los campos obligatorios antes de continuar.
          </v-alert>

          <!-- Alerta de Error de API -->
          <v-alert
            v-if="showApiError"
            type="error"
            variant="tonal"
            class="mx-4 mb-2"
            density="compact"
            closable
            @click:close="showApiError = false"
          >
            {{ apiError }}
          </v-alert>

          <v-divider></v-divider>
          <v-card-actions class="pa-4">
            <v-btn v-if="step > 1" variant="text" @click="prevStep">Atrás</v-btn>
            <v-spacer></v-spacer>
            <v-btn v-if="step < 5" color="primary" @click="validateAndNext">Continuar</v-btn>
            <v-btn v-else color="success" :loading="loading" @click="submitForm">Generar CV</v-btn>
          </v-card-actions>
        </v-stepper>

        <v-card v-if="generatedCv" class="mt-4 pa-4" elevation="2">
          <div class="d-flex justify-space-between align-center mb-4">
            <div>
              <h3 class="text-h6 mb-1">CV generado con éxito</h3>
              <p class="mb-0">Haz clic en el botón para descargar el archivo JSON.</p>
            </div>
            <v-btn color="primary" @click="downloadJson">Descargar JSON</v-btn>
          </div>
          <v-divider class="mb-4"></v-divider>
          <pre class="pa-3" style="max-height: 320px; overflow:auto; background:#f9f9f9; border-radius:8px;">
{{ JSON.stringify(generatedCv, null, 2) }}
          </pre>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import httpClient from '@/http-common.js';
import authService from '@/services/auth.service.js';

export default {
  name: 'FormView',
  data: () => ({
    step: 1,
    loading: false,
    valid: false,
    showValidationError: false,
    showApiError: false,
    apiError: '',
    generatedCv: null,
    steps: ['Contacto', 'Perfil', 'Experiencia', 'Formación', 'Confirmar'],
    rules: {
      required: value => !!value || 'Este campo es obligatorio.',
      email: value => {
        const pattern = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return pattern.test(value) || 'Correo electrónico no válido.';
      },
    },
    userId: authService.getCurrentUser()?.id || (crypto.randomUUID ? crypto.randomUUID() : `user-${Date.now()}-${Math.floor(Math.random() * 1000000)}`),
    form: {
      personal: { 
        nombre_completo: '', 
        profesion: '', 
        email: '', 
        telefono: '', 
        linkedin: '',
        rut: '',
        ciudad: ''
      },
      perfil: { 
        anios_experiencia: 0, 
        experticia: '', 
        propuesta_valor: '' 
      },
      experiencias: [
        { cargo: '', empresa: '', periodo: '', pais: '', descripcion: '', logros: '' }
      ],
      formacion: [
        { titulo: '', institucion: '', periodo: '' }
      ],
      habilidades: ''
    }
  }),
  methods: {
    addExp() {
      this.form.experiencias.push({ cargo: '', empresa: '', periodo: '', pais: '', descripcion: '', logros: '' });
    },
    removeExp(index) {
      this.form.experiencias.splice(index, 1);
    },
    addEdu() {
      this.form.formacion.push({ titulo: '', institucion: '', periodo: '' });
    },
    removeEdu(index) {
      this.form.formacion.splice(index, 1);
    },
    async validateAndNext() {
      const currentForm = this.$refs[`formStep${this.step}`];
      if (currentForm) {
        const { valid } = await currentForm.validate();
        if (valid) {
          this.showValidationError = false;
          this.step++;
        } else {
          this.showValidationError = true;
        }
      }
    },
    prevStep() {
      this.showValidationError = false;
      this.step--;
    },
    async submitForm() {
      if (!this.valid) {
        this.showValidationError = true;
        return;
      }
      this.loading = true;
      try {
        const payload = {
          user_id: this.userId,
          ...this.form,
        };

        const response = await httpClient.post('/api/cv/generate', payload);
        //this.generatedCv = response.data;
        const cleanData = JSON.parse(JSON.stringify(response.data));

        this.generatedCv = cleanData;

        this.$router.push({
          name: 'pdf',
          state: {dataLlm: cleanData}
        });

        console.log('Respuesta de la IA:', response.data);
      } catch (error) {
        console.error('Error al enviar:', error);
        this.apiError = error.userMessage || 'Ha ocurrido un error inesperado.';
        this.showApiError = true;
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } finally {
        this.loading = false;
      }
    },
    downloadJson() {
      if (!this.generatedCv) return;
      const jsonString = JSON.stringify(this.generatedCv, null, 2);
      const blob = new Blob([jsonString], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `cv-${this.userId}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }
  }
}
</script>