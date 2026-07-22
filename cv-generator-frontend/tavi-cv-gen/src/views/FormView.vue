<template>
  <v-container class="py-10">
    <v-row justify="center">
      <v-col cols="12" md="10" lg="8">
        <h2 class="text-h4 mb-6 text-center">Formulario de Generación de CV</h2>

        <!-- ========================================== -->
        <!-- ZONA DE DEBUG: SIMULAR POSTMAN + IA        -->
        <!-- (Atajo: Ctrl + Shift + D)                  -->
        <!-- ========================================== -->
        <v-card v-if="showDebugZone" class="mb-6 pa-4 border-dashed" style="border-color: #ff5252; border-width: 2px;" variant="outlined">
          <div class="d-flex align-center mb-2">
            <v-icon color="error" class="mr-2">mdi-robot-outline</v-icon>
            <h3 class="text-error mb-0">Zona de Debug: Ejecutar IA desde JSON</h3>
          </div>
          <p class="text-caption mb-3">Pega el JSON de entrada (Request). El sistema llenará el formulario y enviará los datos automáticamente a tu backend (RAG + LLM).</p>
          <v-textarea
            v-model="debugJson"
            label="Pega el JSON de entrada aquí..."
            variant="outlined"
            rows="5"
            bg-color="#fff8f8"
          />
          <v-btn color="error" @click="ejecutarProcesoIA" :loading="loading">
            Generar CV con IA
          </v-btn>
        </v-card>
        <!-- ========================================== -->

        <v-stepper v-model="step" :mobile="false">
          <v-stepper-header>
            <template v-for="n in steps.length" :key="n">
              <v-stepper-item :title="steps[n-1]" :value="n" :complete="step > n" />
              <v-divider v-if="n !== steps.length" />
            </template>
          </v-stepper-header>

          <v-stepper-window>
            <!-- Paso 1: Contacto -->
            <v-stepper-window-item :value="1">
              <v-form ref="formStep1" @submit.prevent>
                <v-card title="Información Personal" flat class="pa-4">
                  <v-alert
                    v-if="showValidationError && step === 1"
                    type="error"
                    variant="tonal"
                    dense
                    class="mb-4"
                    border="left"
                  >
                    Revisa los campos obligatorios marcados en rojo y completa los datos faltantes.
                  </v-alert>

                  <v-row>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="form.personal.nombre_completo"
                        label="Nombre Completo *"
                        :rules="[rules.required, rules.minLength(3), rules.maxLength(120)]"
                        variant="outlined"
                        autocomplete="name"
                        counter="120"
                      />
                    </v-col>

                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="form.personal.profesion"
                        label="Profesión / Cargo *"
                        :rules="[rules.required, rules.minLength(2), rules.maxLength(80)]"
                        variant="outlined"
                        counter="80"
                      />
                    </v-col>

                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="form.personal.rut"
                        label="RUT *"
                        :rules="[rules.required, rules.rut]"
                        variant="outlined"
                        placeholder="12.345.678-K"
                        hint="Formato: 12345678-9 o 12.345.678-K"
                        persistent-hint
                      />
                    </v-col>

                    <v-col cols="12" md="6">
                      <v-select
                        v-model="form.personal.ciudad"
                        label="Ciudad *"
                        :items="ciudadesCl"
                        :rules="[rules.required]"
                        variant="outlined"
                        placeholder="Selecciona tu ciudad"
                      />
                    </v-col>

                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="form.personal.email"
                        label="Correo Electrónico *"
                        :rules="[rules.required, rules.email]"
                        variant="outlined"
                        autocomplete="email"
                        type="email"
                        inputmode="email"
                      />
                    </v-col>

                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="form.personal.telefono"
                        label="Teléfono *"
                        :rules="[rules.required, rules.phone]"
                        variant="outlined"
                        autocomplete="tel"
                        type="tel"
                        inputmode="tel"
                        placeholder="+56 9 1234 5678"
                        hint="Incluye código de país"
                        persistent-hint
                      />
                    </v-col>

                    <v-col cols="12">
                      <v-text-field
                        v-model="form.personal.linkedin"
                        label="URL LinkedIn (Opcional)"
                        :rules="[rules.urlLinkedin]"
                        variant="outlined"
                        placeholder="https://www.linkedin.com/in/usuario"
                        prepend-inner-icon="mdi-linkedin"
                      />
                    </v-col>
                  </v-row>
                </v-card>
              </v-form>
            </v-stepper-window-item>

            <!-- Paso 2: Perfil y Habilidades -->
            <v-stepper-window-item :value="2">
              <v-form ref="formStep2" @submit.prevent>
                <v-card title="Perfil Profesional y Habilidades" flat class="pa-4">
                  <v-alert
                    v-if="showValidationError && step === 2"
                    type="error"
                    variant="tonal"
                    dense
                    class="mb-4"
                    border="left"
                  >
                    Completa la información de perfil y habilidades con datos reales y claros.
                  </v-alert>

                  <div class="mb-4">
                    <div class="d-flex align-center justify-space-between mb-1">
                      <span class="text-body-1">Años de experiencia</span>
                      <v-chip color="primary" size="small">
                        {{ form.perfil.anios_experiencia }} años
                      </v-chip>
                    </div>
                    <v-slider
                      v-model="form.perfil.anios_experiencia"
                      min="0"
                      max="50"
                      step="1"
                      thumb-label
                      color="primary"
                      show-ticks="always"
                      tick-size="4"
                    />
                  </div>

                  <v-textarea
                    v-model="form.perfil.experticia"
                    label="Tus áreas de experticia *"
                    :rules="[rules.required, rules.minLength(20), rules.maxLength(400)]"
                    variant="outlined"
                    rows="3"
                    counter="400"
                    hint="Describe las áreas en las que te especializas."
                    persistent-hint
                  />

                  <v-textarea
                    v-model="form.perfil.propuesta_valor"
                    label="Tu propuesta de valor *"
                    :rules="[rules.required, rules.minLength(20), rules.maxLength(500)]"
                    variant="outlined"
                    rows="3"
                    counter="500"
                  >
                    <template #append>
                      <v-tooltip location="top" text="Enfócate en el área o trabajo que tienes en la mira.">
                        <template #activator="{ props }">
                          <v-icon v-bind="props" icon="mdi-help-circle-outline" color="primary" />
                        </template>
                      </v-tooltip>
                    </template>
                  </v-textarea>

                  <v-textarea
                    v-model="form.habilidades"
                    label="Habilidades Técnicas e Idiomas *"
                    :rules="[rules.required, rules.minLength(15), rules.maxLength(800)]"
                    variant="outlined"
                    rows="3"
                    counter="800"
                    placeholder="Ej: Python (Avanzado), Inglés (B2), Excel (Intermedio)"
                    hint="Separa por comas. Indica software/idioma seguido de tu nivel."
                    persistent-hint
                  >
                    <template #append>
                      <v-tooltip location="top" text="Indica el software o idioma seguido de tu nivel de dominio.">
                        <template #activator="{ props }">
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
              <v-form ref="formStep3" @submit.prevent>
                <v-card title="Trayectoria Profesional" flat class="pa-4">
                  <v-alert
                    v-if="showValidationError && step === 3"
                    type="error"
                    variant="tonal"
                    dense
                    class="mb-4"
                    border="left"
                  >
                    Completa todas las experiencias con cargo, empresa, periodo y descripción.
                  </v-alert>

                  <div
                    v-for="(exp, index) in form.experiencias"
                    :key="index"
                    class="mb-6 pa-4 border rounded"
                  >
                    <div class="d-flex justify-space-between align-center mb-2">
                      <span class="text-subtitle-1 font-weight-bold">Experiencia #{{ index + 1 }}</span>
                      <v-btn
                        icon="mdi-delete"
                        size="small"
                        color="error"
                        variant="text"
                        :disabled="form.experiencias.length === 1"
                        @click="removeExp(index)"
                      />
                    </div>

                    <v-row>
                      <v-col cols="12" md="6">
                        <v-text-field
                          v-model="exp.cargo"
                          label="Cargo *"
                          :rules="[rules.required, rules.maxLength(100)]"
                          variant="outlined"
                          counter="100"
                        />
                      </v-col>

                      <v-col cols="12" md="6">
                        <v-text-field
                          v-model="exp.empresa"
                          label="Empresa *"
                          :rules="[rules.required, rules.maxLength(100)]"
                          variant="outlined"
                          counter="100"
                        />
                      </v-col>

                      <!-- Fechas reales en lugar de texto libre -->
                      <v-col cols="12" md="6">
                        <v-text-field
                          v-model="exp.fecha_inicio"
                          label="Fecha de inicio *"
                          type="month"
                          :rules="[rules.required, rules.notFutureMonth]"
                          variant="outlined"
                          placeholder="YYYY-MM"
                          hint="Selecciona el mes y año de inicio"
                          persistent-hint
                          maxlength="7"
                        />
                      </v-col>

                      <v-col cols="12" md="6">
                        <v-switch
                          v-model="exp.trabajo_actual"
                          color="primary"
                          label="Trabajo actual"
                          hide-details
                          class="mb-2"
                        />
                        <v-text-field
                          v-if="!exp.trabajo_actual"
                          v-model="exp.fecha_fin"
                          label="Fecha de término *"
                          type="month"
                          :rules="[rules.required, rules.notFutureMonth]"
                          variant="outlined"
                          placeholder="YYYY-MM"
                          maxlength="7"
                        />
                        <v-text-field
                          v-else
                          model-value="Actualidad"
                          label="Fecha de término"
                          variant="outlined"
                          readonly
                          disabled
                        />
                      </v-col>

                      <!-- Periodo calculado (solo lectura) -->
                      <v-col cols="12" md="6">
                        <v-text-field
                          :model-value="formatPeriodo(exp)"
                          label="Periodo (calculado)"
                          variant="outlined"
                          readonly
                          hint="Calculado en base a las fechas seleccionadas"
                          persistent-hint
                        />
                      </v-col>

                      <v-col cols="12" md="6">
                        <v-select
                          v-model="exp.pais"
                          label="País *"
                          :items="paises"
                          :rules="[rules.required]"
                          variant="outlined"
                          placeholder="Selecciona el país"
                        />
                      </v-col>

                      <v-col cols="12">
                        <v-textarea
                          v-model="exp.descripcion"
                          label="Descripción de funciones *"
                          :rules="[rules.required, rules.minLength(20), rules.maxLength(800)]"
                          variant="outlined"
                          rows="2"
                          counter="800"
                          hint="Describe tus principales responsabilidades."
                          persistent-hint
                        />
                      </v-col>

                      <v-col cols="12">
                        <v-textarea
                          v-model="exp.logros"
                          label="Logros destacados (Opcional)"
                          :rules="[rules.maxLength(800)]"
                          variant="outlined"
                          rows="2"
                          counter="800"
                          hint="Incluye logros medibles si los tienes. Ej: 'Aumenté ventas en 30%'."
                          persistent-hint
                        />
                      </v-col>
                    </v-row>
                  </div>

                  <v-btn
                    prepend-icon="mdi-plus"
                    variant="tonal"
                    color="primary"
                    @click="addExp"
                  >
                    Agregar otra experiencia
                  </v-btn>
                </v-card>
              </v-form>
            </v-stepper-window-item>

            <!-- Paso 4: Formación -->
            <v-stepper-window-item :value="4">
              <v-form ref="formStep4" @submit.prevent>
                <v-card title="Formación Educativa" flat class="pa-4">
                  <v-alert
                    v-if="showValidationError && step === 4"
                    type="error"
                    variant="tonal"
                    dense
                    class="mb-4"
                    border="left"
                  >
                    Completa todos los datos de tu formación antes de continuar.
                  </v-alert>

                  <div
                    v-for="(edu, index) in form.formacion"
                    :key="index"
                    class="mb-6 pa-4 border rounded"
                  >
                    <div class="d-flex justify-space-between align-center mb-2">
                      <span class="text-subtitle-1 font-weight-bold">Educación #{{ index + 1 }}</span>
                      <v-btn
                        icon="mdi-delete"
                        size="small"
                        color="error"
                        variant="text"
                        :disabled="form.formacion.length === 1"
                        @click="removeEdu(index)"
                      />
                    </div>

                    <v-row>
                      <v-col cols="12" md="6">
                        <v-text-field
                          v-model="edu.titulo"
                          label="Título / Diploma *"
                          :rules="[rules.required, rules.maxLength(120)]"
                          variant="outlined"
                          counter="120"
                        />
                      </v-col>

                      <v-col cols="12" md="6">
                        <v-text-field
                          v-model="edu.institucion"
                          label="Institución *"
                          :rules="[rules.required, rules.maxLength(120)]"
                          variant="outlined"
                          counter="120"
                        />
                      </v-col>

                      <v-col cols="12" md="6">
                        <v-text-field
                          v-model="edu.fecha_inicio"
                          label="Fecha de inicio *"
                          type="month"
                          :rules="[rules.required, rules.notFutureMonth]"
                          variant="outlined"
                          placeholder="YYYY-MM"
                          maxlength="7"
                        />
                      </v-col>

                      <v-col cols="12" md="6">
                        <v-switch
                          v-model="edu.en_curso"
                          color="primary"
                          label="Estudio en curso"
                          hide-details
                          class="mb-2"
                        />
                        <v-text-field
                          v-if="!edu.en_curso"
                          v-model="edu.fecha_fin"
                          label="Fecha de término *"
                          type="month"
                          :rules="[rules.required, rules.notFutureMonth]"
                          variant="outlined"
                          placeholder="YYYY-MM"
                          maxlength="7"
                        />
                        <v-text-field
                          v-else
                          model-value="Actualidad"
                          label="Fecha de término"
                          variant="outlined"
                          readonly
                          disabled
                        />
                      </v-col>

                      <!-- Periodo calculado -->
                      <v-col cols="12">
                        <v-text-field
                          :model-value="formatPeriodoEdu(edu)"
                          label="Periodo (calculado)"
                          variant="outlined"
                          readonly
                          hint="Calculado en base a las fechas seleccionadas"
                          persistent-hint
                        />
                      </v-col>
                    </v-row>
                  </div>

                  <v-btn
                    prepend-icon="mdi-plus"
                    variant="tonal"
                    color="primary"
                    @click="addEdu"
                  >
                    Agregar otra formación
                  </v-btn>
                </v-card>
              </v-form>
            </v-stepper-window-item>

            <!-- Paso 5: Finalizar -->
            <v-stepper-window-item :value="5">
              <v-card title="Finalizar y Enviar" flat class="pa-4">
                <v-alert
                  v-if="showValidationError && step === 5"
                  type="error"
                  variant="tonal"
                  dense
                  class="mb-4"
                  border="left"
                >
                  Debes confirmar que la información es correcta antes de generar tu CV.
                </v-alert>

                <p class="mb-4">Revisa tus datos antes de enviar a la IA.</p>
                <v-checkbox
                  v-model="valid"
                  :rules="[(v) => !!v || 'Debes confirmar para continuar']"
                  color="primary"
                  label="Confirmo que la información es correcta"
                />
              </v-card>
            </v-stepper-window-item>
          </v-stepper-window>

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

          <v-divider />
          <v-card-actions class="pa-4">
            <v-btn v-if="step > 1" variant="text" @click="prevStep">Atrás</v-btn>
            <v-spacer />
            <v-btn v-if="step < 5" color="primary" @click="validateAndNext">Continuar</v-btn>
            <v-btn v-else color="success" :loading="loading" @click="submitForm">
              Generar CV
            </v-btn>
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
          <v-divider class="mb-4" />
          <pre class="pa-3" style="max-height: 320px; overflow:auto; background:#f9f9f9; border-radius:8px;">{{ JSON.stringify(generatedCv, null, 2) }}</pre>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import httpClient from '@/http-common.js';
import authService from '@/services/auth.service.js';

// Validador reutilizable para RUT chileno
const validateRut = (rut) => {
  if (!rut) return false;
  const limpio = String(rut).replace(/\./g, '').replace(/-/g, '').trim().toUpperCase();
  if (limpio.length < 2) return false;
  const cuerpo = limpio.slice(0, -1);
  const dv = limpio.slice(-1);

  if (!/^\d+$/.test(cuerpo)) return false;
  if (!/^[0-9K]$/.test(dv)) return false;

  let suma = 0;
  let mult = 2;
  for (let i = cuerpo.length - 1; i >= 0; i--) {
    suma += parseInt(cuerpo[i], 10) * mult;
    mult = mult === 7 ? 2 : mult + 1;
  }
  const resto = suma % 11;
  const dvEsperado = resto === 1 ? 'K' : resto === 0 ? '0' : String(11 - resto);
  return dv === dvEsperado;
};

const formatRut = (rut) => {
  if (!rut) return '';
  const limpio = String(rut).replace(/\./g, '').replace(/-/g, '').trim().toUpperCase();
  if (limpio.length < 2) return limpio;
  const cuerpo = limpio.slice(0, -1);
  const dv = limpio.slice(-1);
  const conPuntos = cuerpo.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return `${conPuntos}-${dv}`;
};

const formatPhone = (phone) => {
  if (!phone) return '';
  const digitos = String(phone).replace(/\D/g, '');
  if (!digitos) return '';
  if (digitos.length === 9) return `+56 9 ${digitos.slice(0, 4)} ${digitos.slice(4)}`;
  if (digitos.length === 11 && digitos.startsWith('56')) {
    return `+${digitos.slice(0, 2)} ${digitos[2]} ${digitos.slice(3, 7)} ${digitos.slice(7)}`;
  }
  return phone;
};

const monthLabel = (yyyyMm) => {
  if (!yyyyMm || !/^\d{4}-\d{2}$/.test(yyyyMm)) return '';
  const [y, m] = yyyyMm.split('-').map(Number);
  const meses = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
  ];
  return `${meses[m - 1] || ''} ${y}`.trim();
};

const ciudadesCl = [
  'Arica', 'Iquique', 'Antofagasta', 'Copiapó', 'La Serena', 'Valparaíso',
  'Santiago', 'Rancagua', 'Talca', 'Chillán', 'Concepción', 'Temuco',
  'Valdivia', 'Puerto Montt', 'Coyhaique', 'Punta Arenas',
];

const paises = [
  'Chile', 'Argentina', 'Bolivia', 'Brasil', 'Colombia', 'Costa Rica',
  'Cuba', 'Ecuador', 'El Salvador', 'España', 'Estados Unidos', 'Guatemala',
  'Honduras', 'México', 'Nicaragua', 'Panamá', 'Paraguay', 'Perú',
  'Puerto Rico', 'República Dominicana', 'Uruguay', 'Venezuela',
  'Alemania', 'Francia', 'Italia', 'Portugal', 'Reino Unido', 'Otro',
];

export default {
  name: 'FormView',
  data: () => ({
    showDebugZone: false,
    debugJson: '',
    step: 1,
    loading: false,
    valid: false,
    showValidationError: false,
    showApiError: false,
    apiError: '',
    generatedCv: null,
    steps: ['Contacto', 'Perfil', 'Experiencia', 'Formación', 'Confirmar'],
    ciudadesCl,
    paises,
    rules: {
      required: (v) => {
        if (v === null || v === undefined) return 'Este campo es obligatorio.';
        if (typeof v === 'string' && !v.trim()) return 'Este campo es obligatorio.';
        return true;
      },
      email: (v) => {
        if (!v) return 'Este campo es obligatorio.';
        const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return pattern.test(String(v).trim()) || 'Correo electrónico no válido.';
      },
      rut: (v) => {
        if (!v) return 'Este campo es obligatorio.';
        return validateRut(v) || 'RUT inválido. Verifica el dígito verificador.';
      },
      phone: (v) => {
        if (!v) return 'Este campo es obligatorio.';
        const digitos = String(v).replace(/\D/g, '');
        if (digitos.length < 8 || digitos.length > 15) {
          return 'Teléfono debe tener entre 8 y 15 dígitos.';
        }
        return true;
      },
      urlLinkedin: (v) => {
        if (!v) return true; // opcional
        const pattern = /^https?:\/\/(www\.)?linkedin\.com\/in\/[A-Za-z0-9._-]+\/?$/;
        return pattern.test(String(v).trim()) || 'URL de LinkedIn no válida. Ej: https://www.linkedin.com/in/usuario';
      },
      minLength: (n) => (v) => {
        if (v == null) return true;
        return String(v).trim().length >= n || `Mínimo ${n} caracteres.`;
      },
      maxLength: (n) => (v) => {
        if (v == null || v === '') return true;
        return String(v).length <= n || `Máximo ${n} caracteres.`;
      },
      notFutureMonth: (v) => {
        if (!v) return true;
        if (!/^\d{4}-\d{2}$/.test(v)) return 'Formato debe ser YYYY-MM.';
        const [y, m] = v.split('-').map(Number);
        const now = new Date();
        const actual = new Date(now.getFullYear(), now.getMonth() + 1, 1);
        const candidato = new Date(y, m, 1);
        return candidato <= actual || 'La fecha no puede ser futura.';
      },
    },
    userId: authService.getCurrentUser()?.id
      || (crypto.randomUUID
        ? crypto.randomUUID()
        : `user-${Date.now()}-${Math.floor(Math.random() * 1000000)}`),
    form: {
      personal: {
        nombre_completo: '',
        profesion: '',
        email: '',
        telefono: '',
        linkedin: '',
        rut: '',
        ciudad: '',
      },
      perfil: {
        anios_experiencia: 0,
        experticia: '',
        propuesta_valor: '',
      },
      experiencias: [
        {
          cargo: '',
          empresa: '',
          pais: '',
          fecha_inicio: '',
          fecha_fin: '',
          trabajo_actual: false,
          periodo: '', // calculado
          descripcion: '',
          logros: '',
        },
      ],
      formacion: [
        {
          titulo: '',
          institucion: '',
          fecha_inicio: '',
          fecha_fin: '',
          en_curso: false,
          periodo: '', // calculado
        },
      ],
      habilidades: '',
    },
  }),
  watch: {
    'form.personal.rut'(v) {
      if (v) this.form.personal.rut = formatRut(v);
    },
    'form.personal.telefono'(v) {
      if (!v) return;
      // sólo reformatea si el usuario no está escribiendo a media palabra
      const digitos = String(v).replace(/\D/g, '');
      if (digitos.length === 9 || (digitos.length >= 11 && digitos.startsWith('56'))) {
        this.form.personal.telefono = formatPhone(v);
      }
    },
    'form.experiencias': {
      deep: true,
      handler() {
        this.form.experiencias.forEach((exp) => {
          exp.periodo = this.formatPeriodo(exp);
        });
      },
    },
    'form.formacion': {
      deep: true,
      handler() {
        this.form.formacion.forEach((edu) => {
          edu.periodo = this.formatPeriodoEdu(edu);
        });
      },
    },
  },

  mounted() {
    // Cuando el componente carga, empezamos a escuchar el teclado
    window.addEventListener('keydown', this.detectarAtajoDebug);
  },
  beforeUnmount() {
    // Cuando cambiamos de página, apagamos el escuchador
    window.removeEventListener('keydown', this.detectarAtajoDebug);
  },

  methods: {
    detectarAtajoDebug(event) {
      if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'd') {
        event.preventDefault();
        this.showDebugZone = !this.showDebugZone;
      }
    },
    
    async ejecutarProcesoIA() {
      try {
        if (!this.debugJson.trim()) {
          alert('El textarea está vacío. Pega un JSON de entrada primero.');
          return;
        }
        
        // Convertimos el JSON pegado
        const inputData = JSON.parse(this.debugJson);
        
        // Llenamos el formulario
        if (inputData.personal) this.form.personal = { ...this.form.personal, ...inputData.personal };
        if (inputData.perfil) this.form.perfil = { ...this.form.perfil, ...inputData.perfil };
        
        // Aseguramos que los arreglos se copien correctamente para evitar errores en Vue
        if (inputData.experiencias) {
          this.form.experiencias = inputData.experiencias.map(exp => ({ ...exp }));
        }
        if (inputData.formacion) {
          this.form.formacion = inputData.formacion.map(edu => ({ ...edu }));
        }
        if (inputData.habilidades) this.form.habilidades = inputData.habilidades;

        // Saltamos visualmente al paso 5 y marcamos el checkbox de confirmación
        this.step = 5;
        this.valid = true;

        await this.$nextTick(); 
        await new Promise(resolve => setTimeout(resolve, 150));

        // Llamamos
        await this.submitForm();
        
      } catch (error) {
        alert('Error: El texto pegado no es un JSON válido.');
        console.error('Error parseando JSON de entrada:', error);
      }
    },
    
    formatPeriodo(exp) {
      const ini = monthLabel(exp.fecha_inicio);
      if (!ini) return '';
      const fin = exp.trabajo_actual
        ? 'Actualidad'
        : monthLabel(exp.fecha_fin);
      if (!fin) return ini;
      return `${ini} - ${fin}`;
    },
    formatPeriodoEdu(edu) {
      const ini = monthLabel(edu.fecha_inicio);
      if (!ini) return '';
      const fin = edu.en_curso ? 'Actualidad' : monthLabel(edu.fecha_fin);
      if (!fin) return ini;
      return `${ini} - ${fin}`;
    },
    addExp() {
      this.form.experiencias.push({
        cargo: '',
        empresa: '',
        pais: '',
        fecha_inicio: '',
        fecha_fin: '',
        trabajo_actual: false,
        periodo: '',
        descripcion: '',
        logros: '',
      });
    },
    removeExp(index) {
      if (this.form.experiencias.length > 1) {
        this.form.experiencias.splice(index, 1);
      }
    },
    addEdu() {
      this.form.formacion.push({
        titulo: '',
        institucion: '',
        fecha_inicio: '',
        fecha_fin: '',
        en_curso: false,
        periodo: '',
      });
    },
    removeEdu(index) {
      if (this.form.formacion.length > 1) {
        this.form.formacion.splice(index, 1);
      }
    },
    async validateStep(stepNumber) {
      const currentForm = this.$refs[`formStep${stepNumber}`];
      if (!currentForm) return true;
      const result = await currentForm.validate();
      return typeof result === 'boolean' ? result : result.valid;
    },
    async validateAndNext() {
      // Validar fechas entre sí antes de pasar
      if (this.step === 3) {
        for (let i = 0; i < this.form.experiencias.length; i++) {
          const exp = this.form.experiencias[i];
          if (exp.fecha_inicio && exp.fecha_fin && !exp.trabajo_actual) {
            if (exp.fecha_fin < exp.fecha_inicio) {
              this.apiError = `Experiencia #${i + 1}: la fecha de término no puede ser anterior a la de inicio.`;
              this.showApiError = true;
              return;
            }
          }
        }
      }
      if (this.step === 4) {
        for (let i = 0; i < this.form.formacion.length; i++) {
          const edu = this.form.formacion[i];
          if (edu.fecha_inicio && edu.fecha_fin && !edu.en_curso) {
            if (edu.fecha_fin < edu.fecha_inicio) {
              this.apiError = `Educación #${i + 1}: la fecha de término no puede ser anterior a la de inicio.`;
              this.showApiError = true;
              return;
            }
          }
        }
      }

      const valid = await this.validateStep(this.step);
      if (valid) {
        this.showValidationError = false;
        this.step++;
      } else {
        this.showValidationError = true;
      }
    },
    async validateAllSteps() {
      let allValid = true;
      for (let index = 1; index <= 4; index++) {
        // eslint-disable-next-line no-await-in-loop
        const valid = await this.validateStep(index);
        if (!valid) allValid = false;
      }
      return allValid;
    },
    prevStep() {
      this.showValidationError = false;
      this.step--;
    },
    buildPayload() {
      // Enviamos tanto el campo `periodo` calculado como las fechas crudas
      // para que el backend tenga la máxima información.
      const payload = {
        user_id: this.userId,
        personal: { ...this.form.personal },
        perfil: { ...this.form.perfil },
        experiencias: this.form.experiencias.map((e) => ({
          cargo: e.cargo,
          empresa: e.empresa,
          pais: e.pais,
          fecha_inicio: e.fecha_inicio,
          fecha_fin: e.trabajo_actual ? null : e.fecha_fin,
          trabajo_actual: !!e.trabajo_actual,
          periodo: e.periodo,
          descripcion: e.descripcion,
          logros: e.logros,
        })),
        formacion: this.form.formacion.map((edu) => ({
          titulo: edu.titulo,
          institucion: edu.institucion,
          fecha_inicio: edu.fecha_inicio,
          fecha_fin: edu.en_curso ? null : edu.fecha_fin,
          en_curso: !!edu.en_curso,
          periodo: edu.periodo,
        })),
        habilidades: this.form.habilidades,
      };
      return payload;
    },
    async submitForm() {
      const allValid = await this.validateAllSteps();
      if (!allValid || !this.valid) {
        this.showValidationError = true;
        return;
      }
      this.loading = true;
      this.showApiError = false;
      try {
        const payload = this.buildPayload();
        const response = await httpClient.post('/api/cv/generate', payload);
        const cleanData = JSON.parse(JSON.stringify(response.data));
        this.generatedCv = cleanData;
        this.$router.push({
          name: 'pdf',
          state: { dataLlm: cleanData },
        });
        // eslint-disable-next-line no-console
        console.log('Respuesta de la IA:', response.data);
      } catch (error) {
        // eslint-disable-next-line no-console
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
    },
  },
};
</script>
