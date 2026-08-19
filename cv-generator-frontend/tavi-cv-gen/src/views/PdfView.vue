<template>
  <v-container fluid class="pa-4">
    <v-progress-circular v-if="loading" indeterminate color="primary" class="d-block mx-auto mt-5"></v-progress-circular>

    <v-row v-if="cvDat && !loading">
      
      <v-col cols="12" md="5">
        <v-card class="pa-4" elevation="3">
          <v-card-title class="px-0 d-flex align-center justify-space-between flex-wrap gap-2">
            <div class="d-flex align-center">
              <v-icon color="indigo" class="mr-2">mdi-pencil-box-outline</v-icon>
              <span class="text-h6 font-weight-bold">Editar Contenido</span>
            </div>
            
            <div class="d-flex gap-2 mt-2 mt-sm-0">
              <v-btn 
                color="indigo-darken-1" 
                variant="tonal"
                prepend-icon="mdi-open-in-new"
                density="comfortable"
                class="text-none mr-2"
                @click="generatePDF"
              >
                Visualizar
              </v-btn>
              <v-btn 
                color="indigo" 
                prepend-icon="mdi-download"
                density="comfortable"
                class="text-none"
                @click="downloadPDF"
              >
                Descargar PDF
              </v-btn>
            </div>
          </v-card-title>
          
          <v-divider class="my-3" />

          <v-card-text class="px-0">
            <v-expansion-panels variant="accordion">
              
              <v-expansion-panel title="Datos Personales">
                <v-expansion-panel-text class="pt-2">
                  <v-text-field v-model="cvDat.personal.nombre_completo" label="Nombre Completo" variant="outlined" density="compact"></v-text-field>
                  <v-text-field v-model="cvDat.personal.profesion" label="Profesión" variant="outlined" density="compact"></v-text-field>
                  <v-text-field v-model="cvDat.personal.ciudad" label="Ciudad" variant="outlined" density="compact"></v-text-field>
                  <v-text-field v-model="cvDat.personal.telefono" label="Teléfono" variant="outlined" density="compact"></v-text-field>
                </v-expansion-panel-text>
              </v-expansion-panel>

              <v-expansion-panel title="Perfil Profesional">
                <v-expansion-panel-text class="pt-2">
                  <v-textarea v-model="cvDat.perfil.propuesta_valor" label="Propuesta de Valor" variant="outlined" auto-grow rows="3"></v-textarea>
                  <v-text-field v-model="cvDat.perfil.anios_experiencia" label="Años de Experiencia" type="number" variant="outlined" density="compact"></v-text-field>
                  <v-textarea v-model="cvDat.perfil.experticia" label="Experticia" variant="outlined" auto-grow rows="2"></v-textarea>
                </v-expansion-panel-text>
              </v-expansion-panel>

              <v-expansion-panel title="Experiencia Laboral">
                <v-expansion-panel-text class="pt-2">
                  <div v-for="(exp, i) in cvDat.experiencias" :key="i" class="mb-4 border-bottom pb-2">
                    <p class="font-weight-bold text-indigo mb-1">Empresa {{ i + 1 }}</p>
                    <v-text-field v-model="exp.cargo" label="Cargo" variant="outlined" density="compact"></v-text-field>
                    <v-textarea v-model="exp.descripcion" label="Funciones" variant="outlined" auto-grow rows="3"></v-textarea>
                    <v-textarea v-model="exp.logros" label="Logros" variant="outlined" auto-grow rows="2"></v-textarea>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>

              <v-expansion-panel title="Formación Académica">
                <v-expansion-panel-text class="pt-2">
                  <div v-for="(form, i) in cvDat.formacion" :key="i" class="mb-4 border-bottom pb-2">
                    <p class="font-weight-bold text-indigo mb-1">Institución {{ i + 1 }}</p>
                    <v-text-field v-model="form.titulo" label="Título" variant="outlined" density="compact"></v-text-field>
                    <v-text-field v-model="form.institucion" label="Institución" variant="outlined" density="compact"></v-text-field>
                    <v-text-field v-model="form.periodo" label="Periodo (ej: 2019 - 2021)" variant="outlined" density="compact"></v-text-field>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>

        <v-btn
            v-if = "cvDat"
            color = "success"
            @click = "generatePDF"
            class="mr-2"
        >
        Abrir PDF en nueva pestaña
        </v-btn>

        <v-btn
            v-if = "cvDat"
            color = "success"
            @click = "downloadPDF"
            class="mr-2"
        >
            Descargar CV PDF
        </v-btn>

        <v-alert
            v-if="cvDat && cvDat.remaining_days !== undefined"
            type="info"
            variant="tonal"
            class="mt-4"
            prepend-icon="mdi-shield-lock-outline"
        >
            Este CV se eliminará automáticamente por protección de datos
            el {{ formatExpiration(cvDat.expires_at) }}
            (quedan {{ cvDat.remaining_days }} día{{ cvDat.remaining_days === 1 ? '' : 's' }}).
        </v-alert>

        <v-card v-if="cvDat && !loading" class="mt-4">
            <v-card-title>Vista Previa del CV</v-card-title>
            <v-card-text>
                <div class="cv-preview pa-6">
                    <div class="text-center mb-4">
                        <h1 class="text-h4 font-weight-bold">{{ cvDat.personal.nombre_completo }}</h1>
                        <h2 class="text-h6 text-medium-emphasis">{{ cvDat.personal.profesion }}</h2>
                        <p class="text-caption text-grey">
                            {{ cvDat.personal.email }} | {{ cvDat.personal.telefono }} | {{ cvDat.personal.ciudad }}
                        </p>
                        <p class="text-caption text-grey">
                            Rut: {{ cvDat.personal.rut }}{{ cvDat.personal.linkedin ? ' | LinkedIn: ' + cvDat.personal.linkedin : '' }}
                        </p>
                    </div>

                    <v-divider class="mb-4" />

                    <h3 class="text-subtitle-1 font-weight-bold text-decoration-underline mb-2">Perfil Profesional</h3>
                    <p class="text-body-2 mb-1">{{ cvDat.perfil.propuesta_valor }}</p>
                    <p class="text-body-2 mb-1">Años de experiencia: {{ cvDat.perfil.anios_experiencia }}</p>
                    <p class="text-body-2 mb-4">Experticia: {{ cvDat.perfil.experticia }}</p>

                    <h3 class="text-subtitle-1 font-weight-bold text-decoration-underline mb-2">Experiencia Laboral</h3>
                    <div v-for="(exp, i) in cvDat.experiencias" :key="i" class="mb-3">
                        <p class="text-body-2 font-weight-bold mb-0">{{ exp.cargo }} - {{ exp.empresa }}</p>
                        <p class="text-caption font-italic mb-0">{{ exp.periodo }} | {{ exp.pais }}</p>
                        <p class="text-body-2 mb-0">Funciones: {{ exp.descripcion }}</p>
                        <p v-if="exp.logros" class="text-body-2 mb-0">Logros: {{ exp.logros }}</p>
                    </div>

                    <h3 class="text-subtitle-1 font-weight-bold text-decoration-underline mb-2">Formación Académica</h3>
                    <p v-for="(form, i) in cvDat.formacion" :key="i" class="text-body-2 mb-1">
                        {{ form.titulo }} en {{ form.institucion }} ({{ form.periodo }})
                    </p>

                    <h3 class="text-subtitle-1 font-weight-bold text-decoration-underline mb-2 mt-4">Habilidades</h3>
                    <p class="text-body-2">{{ cvDat.habilidades }}</p>
                </div>
            </v-card-text>
        </v-card>
      </v-col>

      <!-- COLUMNA DERECHA: LA VISTA PREVIA A4 -->
        <v-col cols="12" md="7" class="bg-grey-lighten-4 pt-4 pb-8" style="overflow-y: auto; max-height: 88vh;">
        <div class="a4-preview pa-8 pa-sm-12">
          
          <div class="text-center mb-4">
            <h1 class="text-h4 font-weight-bold mb-1">{{ cvDat.personal.nombre_completo }}</h1>
            <h2 class="text-subtitle-1 text-medium-emphasis mb-2">{{ cvDat.personal.profesion }}</h2>
            <p class="text-caption text-grey mb-1">
              {{ cvDat.personal.email }} | {{ cvDat.personal.telefono }} | {{ cvDat.personal.ciudad }}
            </p>
            <p class="text-caption text-grey">
              Rut: {{ cvDat.personal.rut }} | LinkedIn: {{ cvDat.personal.linkedin }}
            </p>
          </div>
          
          <v-divider class="mb-4" />

          <h3 class="text-body-1 font-weight-bold text-decoration-underline mb-2">Perfil Profesional</h3>
          <p class="text-body-2 mb-2">{{ cvDat.perfil.propuesta_valor }}</p>
          <p class="text-body-2 mb-1"><strong>Años de experiencia:</strong> {{ cvDat.perfil.anios_experiencia }}</p>
          <p class="text-body-2 mb-4"><strong>Experticia:</strong> {{ cvDat.perfil.experticia }}</p>

          <h3 class="text-body-1 font-weight-bold text-decoration-underline mb-2">Experiencia Laboral</h3>
          <div v-for="(exp, i) in cvDat.experiencias" :key="i" class="mb-4">
            <p class="text-body-2 font-weight-bold mb-0">{{ exp.cargo }} - {{ exp.empresa }}</p>
            <p class="text-caption font-italic text-grey mb-1">{{ exp.periodo }} | {{ exp.pais }}</p>
            <p class="text-body-2 mb-1"><strong>Funciones:</strong> {{ exp.descripcion }}</p>
            <p v-if="exp.logros" class="text-body-2 mb-0"><strong>Logros:</strong> {{ exp.logros }}</p>
          </div>

          <h3 class="text-body-1 font-weight-bold text-decoration-underline mb-2 mt-4">Formación Académica</h3>
          <div v-for="(form, i) in cvDat.formacion" :key="i" class="mb-2">
            <p class="text-body-2 mb-0">
              {{ form.titulo}} en <strong>{{ form.institucion }}</strong> ({{ form.periodo }})
            </p>
          </div>

          <h3 class="text-body-1 font-weight-bold text-decoration-underline mb-2 mt-4">Habilidades</h3>
          <ul class="pl-4">
            <li v-for="(hab, i) in cvDat.habilidades.split('|')" :key="i" class="text-body-2 mb-1">
              {{ hab.trim() }}
            </li>
          </ul>

        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
    import pdfMake from "pdfmake/build/pdfmake";
    import pdfFonts from "pdfmake/build/vfs_fonts";
    import httpClient from "@/http-common.js";

    pdfMake.vfs = pdfFonts && pdfFonts.pdfMake ? pdfFonts.pdfMake.vfs : pdfMake.vfs;

    export default{
        name: 'PdfView',
        props: ['cvId'],
        data () {
            return {
                cvDat: null,
                loading: false
            };
        },

        async mounted() {
            await this.getJson();
        },

        methods: {
            async getJson() {
                this.loading = true;
                try {
                    const cvId = this.cvId || this.$route.params?.cvId;

                    if (cvId) {
                        const res = await httpClient.get(`/api/cv/${cvId}`);
                        this.cvDat = res.data.cv_data;
                    } else {
                        const dLLM = window.history.state;
                        if(dLLM && dLLM.dataLlm){
                            const data = dLLM.dataLlm;
                            this.cvDat = data.cv_data;
                            // la respuesta de /generate trae la retención a nivel raíz
                            if (data.remaining_days !== undefined) {
                                this.cvDat = {
                                    ...this.cvDat,
                                    expires_at: data.expires_at,
                                    remaining_seconds: data.remaining_seconds,
                                    remaining_days: data.remaining_days,
                                };
                            }
                        }
                    }

                    console.log("JSON recibido exitosamente", this.cvDat);
                } 
                catch(error){
                    console.error("Error al cargar el JSON", error);
                }
                finally{
                    this.loading = false;
                }
            },

            formatExpiration(iso){
                if (!iso) return '';
                return new Date(iso).toLocaleDateString('es-CL');
            },

            getFormat(){
                if(!this.cvDat){
                    console.warn("No hay datos para hacer el PDF");
                    return;
                }
                
                return {
                    content: [
                        //PERSONAL
                        { text: this.cvDat.personal.nombre_completo, style: 'header' },
                        { text: this.cvDat.personal.profesion, style: 'subHeader' },
                        { 
                            text: `${this.cvDat.personal.email} | ${this.cvDat.personal.telefono} | ${this.cvDat.personal.ciudad}`, 
                            style: 'contact' 
                        },
                        {
                            text: `Rut: ${this.cvDat.personal.rut} | LinkedIn: ${this.cvDat.personal.linkedin}`,
                            style: 'contact', margin: [0, 0, 0, 10]
                        },

                        //PERFIL
                        { text: 'Perfil Profesional', style: 'sectionTitle' },
                        { text: this.cvDat.perfil.propuesta_valor, style: 'bodyText' },
                        {
                            text: [
                                { text: 'Años de experiencia: ', bold: true },
                                `${this.cvDat.perfil.anios_experiencia}`
                            ],
                            style: 'bodyText',
                            margin: [0, 5, 0, 2]
                        },
                        {
                            text: [
                                { text: 'Experticia: ', bold: true },
                                this.cvDat.perfil.experticia
                            ],
                            style: 'bodyText',
                            margin: [0, 0, 0, 10]
                        },

                        //EXPERIENCIA
                        { text: 'Experiencia Laboral', style: 'sectionTitle' },
                        ...this.cvDat.experiencias.map(exp => ({
                            stack: [
                                {text: `${exp.cargo} - ${exp.empresa}`, bold: true},
                                {text: `${exp.periodo} | ${exp.pais}`, italics: true, fontSize: 10, margin: [0, 0, 0, 4]},
                                {
                                    text: [
                                        { text: 'Funciones: ', bold: true },
                                        exp.descripcion
                                    ],
                                    style: 'bodyText',
                                    margin: [0, 0, 0, 4]
                                },
                                ...(exp.logros ? [{
                                    text: [
                                        { text: 'Logros: ', bold: true },
                                        exp.logros
                                    ],
                                    style: 'bodyText',
                                    margin: [0, 0, 0, 10]
                                }] : [{text: '', margin: [0, 0, 0, 6]}])
                            ],
                            margin: [0, 5, 0, 5]
                        })),

                        //FORMACION
                        { text: 'Formación Académica', style: 'sectionTitle' },
                        ...this.cvDat.formacion.map(form => ({
                            text: [
                                { text: `${form.titulo} en ` },
                                { text: form.institucion, bold: true },
                                { text: ` (${form.periodo})` }
                            ],
                            style: 'bodyText',
                            margin: [0, 2, 0, 2]
                        })),

                        //HABILIDADES
                        { text: 'Habilidades', style: 'sectionTitle' },
                        {
                            ul: this.cvDat.habilidades.split('|').map(item => item.trim()),
                            style: 'bodyText',
                            margin: [10, 0, 0, 5]
                        }
                    ],
                    styles: {
                        header: {fontSize: 22, bold: true, alignment: 'center'},
                        subHeader: {fontSize: 16, alignment: 'center', color: '#555', margin: [0, 0, 0, 10]},
                        contact: {fontSize: 10, alignment: 'center', color: 'gray'},
                        sectionTitle: {fontSize: 14, bold: true, decoration: 'underline', margin: [0, 10, 0, 5]},
                        bodyText: {fontSize: 11, lineHeight: 1.2, margin: [0, 0, 0, 5]}
                    },
                    defaultStyle:{
                        font: 'Roboto'
                    }
                };
            },

            generatePDF(){
                if (!this.cvDat) return;
                const format = this.getFormat();
                pdfMake.createPdf(format).open();
            },

            downloadPDF(){
                if (!this.cvDat) return;
                const format = this.getFormat();
                pdfMake.createPdf(format).download(`CV_ATS_${this.cvDat.personal.nombre_completo}.pdf`);
            }
        }
    }
</script>

<style scoped>
.a4-preview {
    background-color: white;
    width: 100%;
    max-width: 794px; 
    min-height: 1123px; 
    height: max-content; 
    margin: 0 auto; /* Centra la hoja horizontalmente */
    box-shadow: 0px 10px 25px rgba(0, 0, 0, 0.15); 
    border-radius: 2px; 
    box-sizing: border-box; 
    color: #212121; 
    line-height: 1.5;
    text-align: left;
}

/* Helper class para layouts flex compactos */
.gap-2 {
  gap: 8px;
}
</style>