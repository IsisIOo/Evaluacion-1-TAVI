<template>
  <v-container fluid class="pa-4">
    <v-progress-circular v-if="loading" indeterminate color="primary" class="d-block mx-auto mt-5"></v-progress-circular>

    <v-row v-if="cvDat && !loading">
      
      <!-- COLUMNA IZQUIERDA: PANEL DE EDICIÓN -->
      <v-col cols="12" md="5">
        <v-card class="pa-4" elevation="3">
          
          <!-- Botonera Moderna -->
          <v-card-title class="px-0 d-flex align-center justify-space-between flex-wrap gap-2">
            <div class="d-flex align-center">
              <v-icon color="indigo" class="mr-2">mdi-pencil-box-outline</v-icon>
              <span class="text-h6 font-weight-bold">Editar Contenido</span>
            </div>
            
            <div class="d-flex gap-2 mt-2 mt-sm-0">
              <v-btn color="indigo-darken-1" variant="tonal" prepend-icon="mdi-open-in-new" density="comfortable" class="text-none mr-2" @click="generatePDF">
                Visualizar
              </v-btn>
              <v-btn color="indigo" prepend-icon="mdi-download" density="comfortable" class="text-none" @click="downloadPDF">
                Descargar PDF
              </v-btn>
            </div>
          </v-card-title>
          
          <v-divider class="my-3" />

          <v-card-text class="px-0">
            <!-- ALERTA DE PRIVACIDAD INTEGRADA AL DISEÑO -->
            <v-alert
              v-if="cvDat.remaining_days !== undefined"
              type="info"
              variant="tonal"
              class="mb-4"
              density="compact"
              prepend-icon="mdi-shield-lock-outline"
            >
              Por protección de datos, este CV se eliminará el <strong>{{ formatExpiration(cvDat.expires_at) }}</strong> 
              (quedan {{ cvDat.remaining_days }} día{{ cvDat.remaining_days === 1 ? '' : 's' }}).
            </v-alert>

            <!-- SELECTOR DE PLANTILLAS -->
            <div class="mb-4">
              <p class="text-subtitle-2 text-medium-emphasis mb-2">Diseño del Currículum:</p>
              <v-btn-toggle
                v-model="selectedTemplate"
                color="indigo"
                mandatory
                class="w-100 border flex-wrap"
                density="comfortable"
              >
                <v-btn value="tradicional" class="flex-grow-1 text-none px-2">
                  <v-icon start>mdi-file-document-outline</v-icon>
                  Tradicional
                </v-btn>
                <v-btn value="moderno" class="flex-grow-1 text-none px-2">
                  <v-icon start>mdi-palette-outline</v-icon>
                  Moderno
                </v-btn>
                <v-btn value="corporativo" class="flex-grow-1 text-none px-2">
                  <v-icon start>mdi-briefcase-outline</v-icon>
                  Corporativo
                </v-btn>
              </v-btn-toggle>
            </div>

            <!-- PANELES DE EDICIÓN -->
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

            </v-expansion-panels>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- COLUMNA DERECHA: LA VISTA PREVIA A4 -->
      <v-col cols="12" md="7" class="bg-grey-lighten-4 pt-4 pb-8" style="overflow-y: auto; height: 100dvh;">
        <div class="a4-preview pa-0" :class="`theme-${selectedTemplate}`">
          
          <!-- ENCABEZADO -->
          <div class="cv-header pa-8">
            <h1 class="text-h4 font-weight-bold mb-1 header-name">{{ cvDat.personal.nombre_completo }}</h1>
            <h2 class="text-subtitle-1 mb-2 header-title">{{ cvDat.personal.profesion }}</h2>
            <p class="text-caption mb-1 header-contact">
              {{ cvDat.personal.email }} | {{ cvDat.personal.telefono }} | {{ cvDat.personal.ciudad }}
            </p>
            <p class="text-caption header-contact">
              Rut: {{ cvDat.personal.rut }} | LinkedIn: {{ cvDat.personal.linkedin }}
            </p>
          </div>
          
          <v-divider v-if="selectedTemplate === 'tradicional'" class="mx-8 mb-4" />

          <!-- CUERPO -->
          <div class="cv-body px-8 pb-8 mt-4">
            <h3 class="section-title text-body-1 font-weight-bold mb-3">Perfil Profesional</h3>
            <p class="text-body-2 mb-2">{{ cvDat.perfil.propuesta_valor }}</p>
            <p class="text-body-2 mb-1"><strong>Años de experiencia:</strong> {{ cvDat.perfil.anios_experiencia }}</p>
            <p class="text-body-2 mb-5"><strong>Experticia:</strong> {{ cvDat.perfil.experticia }}</p>

            <h3 class="section-title text-body-1 font-weight-bold mb-3">Experiencia Laboral</h3>
            <div v-for="(exp, i) in cvDat.experiencias" :key="i" class="mb-4">
              <p class="text-body-2 font-weight-bold mb-0 cargo-text">{{ exp.cargo }} - {{ exp.empresa }}</p>
              <p class="text-caption font-italic mb-1 date-text">{{ exp.periodo }} | {{ exp.pais }}</p>
              <p class="text-body-2 mb-1"><strong>Funciones:</strong> {{ exp.descripcion }}</p>
              <p v-if="exp.logros" class="text-body-2 mb-0"><strong>Logros:</strong> {{ exp.logros }}</p>
            </div>

            <h3 class="section-title text-body-1 font-weight-bold mb-3 mt-5">Formación Académica</h3>
            <div v-for="(form, i) in cvDat.formacion" :key="i" class="mb-2">
              <p class="text-body-2 mb-0">
                {{ form.titulo}} en <strong>{{ form.institucion }}</strong> ({{ form.periodo }})
              </p>
            </div>

            <h3 class="section-title text-body-1 font-weight-bold mb-3 mt-5">Habilidades</h3>
            <ul class="pl-4">
              <li v-for="(hab, i) in cvDat.habilidades.split('|')" :key="i" class="text-body-2 mb-1">
                {{ hab.trim() }}
              </li>
            </ul>
          </div>

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
                loading: false,
                selectedTemplate: 'tradicional' // Estado por defecto
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
                if(!this.cvDat) return;
                
                if (this.selectedTemplate === 'moderno') return this.getFormatModerno();
                if (this.selectedTemplate === 'corporativo') return this.getFormatCorporativo();
                return this.getFormatTradicional();
            },

            // ==========================================
            // PLANTILLA 1: TRADICIONAL
            // ==========================================
            getFormatTradicional(){
                return {
                    content: [
                        { text: this.cvDat.personal.nombre_completo, style: 'header' },
                        { text: this.cvDat.personal.profesion, style: 'subHeader' },
                        { text: `${this.cvDat.personal.email} | ${this.cvDat.personal.telefono} | ${this.cvDat.personal.ciudad}`, style: 'contact' },
                        { text: `Rut: ${this.cvDat.personal.rut} | LinkedIn: ${this.cvDat.personal.linkedin}`, style: 'contact', margin: [0, 0, 0, 15] },

                        { canvas: [{ type: 'line', x1: 0, y1: 0, x2: 515, y2: 0, lineWidth: 1, lineColor: '#E0E0E0' }], margin: [0, 0, 0, 15] },

                        { text: 'Perfil Profesional', style: 'sectionTitle' },
                        { text: this.cvDat.perfil.propuesta_valor, style: 'bodyText' },
                        { text: [ { text: 'Años de experiencia: ', bold: true }, `${this.cvDat.perfil.anios_experiencia}` ], style: 'bodyText', margin: [0, 5, 0, 2] },
                        { text: [ { text: 'Experticia: ', bold: true }, this.cvDat.perfil.experticia ], style: 'bodyText', margin: [0, 0, 0, 10] },

                        { text: 'Experiencia Laboral', style: 'sectionTitle' },
                        ...this.cvDat.experiencias.map(exp => ({
                            stack: [
                                {text: `${exp.cargo} - ${exp.empresa}`, bold: true},
                                {text: `${exp.periodo} | ${exp.pais}`, italics: true, fontSize: 10, margin: [0, 0, 0, 4]},
                                { text: [ { text: 'Funciones: ', bold: true }, exp.descripcion ], style: 'bodyText', margin: [0, 0, 0, 4] },
                                ...(exp.logros ? [{ text: [ { text: 'Logros: ', bold: true }, exp.logros ], style: 'bodyText', margin: [0, 0, 0, 10] }] : [{text: '', margin: [0, 0, 0, 6]}])
                            ],
                            margin: [0, 5, 0, 5]
                        })),

                        { text: 'Formación Académica', style: 'sectionTitle' },
                        ...this.cvDat.formacion.map(form => ({
                            text: [ { text: `${form.titulo} en ` }, { text: form.institucion, bold: true }, { text: ` (${form.periodo})` } ], style: 'bodyText', margin: [0, 2, 0, 2]
                        })),

                        { text: 'Habilidades', style: 'sectionTitle' },
                        { ul: this.cvDat.habilidades.split('|').map(item => item.trim()), style: 'bodyText', margin: [10, 0, 0, 5] }
                    ],
                    styles: {
                        header: {fontSize: 22, bold: true, alignment: 'center'},
                        subHeader: {fontSize: 16, alignment: 'center', color: '#555', margin: [0, 0, 0, 10]},
                        contact: {fontSize: 10, alignment: 'center', color: 'gray'},
                        sectionTitle: {fontSize: 14, bold: true, decoration: 'underline', margin: [0, 10, 0, 5]},
                        bodyText: {fontSize: 11, lineHeight: 1.2, margin: [0, 0, 0, 5]}
                    },
                    defaultStyle:{ font: 'Roboto' }
                };
            },

            // ==========================================
            // PLANTILLA 2: MODERNO (Azul Indigo)
            // ==========================================
            getFormatModerno(){
                const sectionTitle = (title) => ([
                    { text: title, style: 'sectionTitleMod' },
                    { canvas: [{ type: 'line', x1: 0, y1: 0, x2: 515, y2: 0, lineWidth: 1.5, lineColor: '#3F51B5' }], margin: [0, 0, 0, 10] }
                ]);

                return {
                    pageMargins: [40, 40, 40, 40],
                    content: [
                        {
                            table: {
                                widths: ['*'],
                                body: [
                                    [
                                        {
                                            stack: [
                                                { text: this.cvDat.personal.nombre_completo, style: 'headerMod' },
                                                { text: this.cvDat.personal.profesion, style: 'subHeaderMod' },
                                                { text: `${this.cvDat.personal.email} | ${this.cvDat.personal.telefono} | ${this.cvDat.personal.ciudad}`, style: 'contactMod' },
                                                { text: `Rut: ${this.cvDat.personal.rut} | LinkedIn: ${this.cvDat.personal.linkedin}`, style: 'contactMod' }
                                            ],
                                            fillColor: '#3F51B5', margin: [40, 40, 40, 30], border: [false, false, false, false]
                                        }
                                    ]
                                ]
                            },
                            layout: 'noBorders', margin: [-40, -40, -40, 20] 
                        },

                        ...sectionTitle('Perfil Profesional'),
                        { text: this.cvDat.perfil.propuesta_valor, style: 'bodyText' },
                        { text: [ { text: 'Años de experiencia: ', bold: true }, `${this.cvDat.perfil.anios_experiencia}` ], style: 'bodyText', margin: [0, 5, 0, 2] },
                        { text: [ { text: 'Experticia: ', bold: true }, this.cvDat.perfil.experticia ], style: 'bodyText', margin: [0, 0, 0, 10] },

                        ...sectionTitle('Experiencia Laboral'),
                        ...this.cvDat.experiencias.map(exp => ({
                            stack: [
                                {text: `${exp.cargo} - ${exp.empresa}`, bold: true},
                                {text: `${exp.periodo} | ${exp.pais}`, italics: true, fontSize: 10, margin: [0, 0, 0, 4]},
                                { text: [ { text: 'Funciones: ', bold: true }, exp.descripcion ], style: 'bodyText', margin: [0, 0, 0, 4] },
                                ...(exp.logros ? [{ text: [ { text: 'Logros: ', bold: true }, exp.logros ], style: 'bodyText', margin: [0, 0, 0, 10] }] : [{text: '', margin: [0, 0, 0, 6]}])
                            ],
                            margin: [0, 0, 0, 5]
                        })),

                        ...sectionTitle('Formación Académica'),
                        ...this.cvDat.formacion.map(form => ({
                            text: [ { text: `${form.titulo} en ` }, { text: form.institucion, bold: true }, { text: ` (${form.periodo})` } ], style: 'bodyText', margin: [0, 2, 0, 2]
                        })),

                        ...sectionTitle('Habilidades'),
                        { ul: this.cvDat.habilidades.split('|').map(item => item.trim()), style: 'bodyText', margin: [10, 0, 0, 5] }
                    ],
                    styles: {
                        headerMod: {fontSize: 24, bold: true, color: 'white', alignment: 'center'},
                        subHeaderMod: {fontSize: 14, alignment: 'center', color: '#E8EAF6', margin: [0, 5, 0, 10]},
                        contactMod: {fontSize: 10, alignment: 'center', color: '#C5CAE9'},
                        sectionTitleMod: {fontSize: 14, bold: true, color: '#3F51B5', margin: [0, 15, 0, 4]}, 
                        bodyText: {fontSize: 11, lineHeight: 1.2, margin: [0, 0, 0, 5]}
                    },
                    defaultStyle:{ font: 'Roboto' }
                };
            },

            // ==========================================
            // PLANTILLA 3: CORPORATIVO (Esmeralda oscuro)
            // ==========================================
            getFormatCorporativo(){
                // Truco: Tabla sin bordes para generar la barra lateral izquierda en el título
                const sectionTitle = (title) => ([
                    {
                        table: {
                            widths: [4, '*'],
                            body: [
                                [
                                    { fillColor: '#009688', text: '', border: [false, false, false, false] },
                                    { text: title.toUpperCase(), style: 'sectionTitleCorp', border: [false, false, false, false], margin: [5, 0, 0, 0] }
                                ]
                            ]
                        },
                        layout: 'noBorders', margin: [0, 15, 0, 8]
                    }
                ]);

                return {
                    content: [
                        { text: this.cvDat.personal.nombre_completo, style: 'headerCorp' },
                        { text: this.cvDat.personal.profesion.toUpperCase(), style: 'subHeaderCorp' },
                        { text: `${this.cvDat.personal.email} | ${this.cvDat.personal.telefono} | ${this.cvDat.personal.ciudad}`, style: 'contactCorp' },
                        { text: `Rut: ${this.cvDat.personal.rut} | LinkedIn: ${this.cvDat.personal.linkedin}`, style: 'contactCorp', margin: [0, 0, 0, 10] },
                        
                        { canvas: [{ type: 'line', x1: 0, y1: 0, x2: 515, y2: 0, lineWidth: 2, lineColor: '#009688' }], margin: [0, 0, 0, 15] },

                        ...sectionTitle('Perfil Profesional'),
                        { text: this.cvDat.perfil.propuesta_valor, style: 'bodyText' },
                        { text: [ { text: 'Años de experiencia: ', bold: true }, `${this.cvDat.perfil.anios_experiencia}` ], style: 'bodyText', margin: [0, 5, 0, 2] },
                        { text: [ { text: 'Experticia: ', bold: true }, this.cvDat.perfil.experticia ], style: 'bodyText', margin: [0, 0, 0, 10] },

                        ...sectionTitle('Experiencia Laboral'),
                        ...this.cvDat.experiencias.map(exp => ({
                            stack: [
                                {text: `${exp.cargo} - ${exp.empresa}`, bold: true, color: '#263238'},
                                {text: `${exp.periodo} | ${exp.pais}`, italics: true, fontSize: 10, margin: [0, 0, 0, 4], color: '#009688'},
                                { text: [ { text: 'Funciones: ', bold: true }, exp.descripcion ], style: 'bodyText', margin: [0, 0, 0, 4] },
                                ...(exp.logros ? [{ text: [ { text: 'Logros: ', bold: true }, exp.logros ], style: 'bodyText', margin: [0, 0, 0, 10] }] : [{text: '', margin: [0, 0, 0, 6]}])
                            ],
                            margin: [0, 5, 0, 5]
                        })),

                        ...sectionTitle('Formación Académica'),
                        ...this.cvDat.formacion.map(form => ({
                            text: [ { text: `${form.titulo} en ` }, { text: form.institucion, bold: true }, { text: ` (${form.periodo})` } ], style: 'bodyText', margin: [0, 2, 0, 2]
                        })),

                        ...sectionTitle('Habilidades'),
                        { ul: this.cvDat.habilidades.split('|').map(item => item.trim()), style: 'bodyText', margin: [10, 0, 0, 5] }
                    ],
                    styles: {
                        headerCorp: {fontSize: 26, bold: true, color: '#263238', alignment: 'left'},
                        subHeaderCorp: {fontSize: 12, bold: true, color: '#009688', alignment: 'left', margin: [0, 5, 0, 5], characterSpacing: 1},
                        contactCorp: {fontSize: 10, color: '#546E7A', alignment: 'left'},
                        sectionTitleCorp: {fontSize: 13, bold: true, color: '#263238'},
                        bodyText: {fontSize: 11, lineHeight: 1.2, margin: [0, 0, 0, 5]}
                    },
                    defaultStyle:{ font: 'Roboto' }
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
    margin: 0 auto; 
    box-shadow: 0px 10px 25px rgba(0, 0, 0, 0.15); 
    border-radius: 2px; 
    box-sizing: border-box; 
    color: #212121; 
    line-height: 1.5;
    text-align: left;
}

/* ------------------------------------- */
/* TEMA: TRADICIONAL                     */
/* ------------------------------------- */
.theme-tradicional .cv-header {
    text-align: center;
    background-color: transparent;
    color: #212121;
}
.theme-tradicional .header-title { color: #616161; }
.theme-tradicional .header-contact { color: #9e9e9e; }
.theme-tradicional .date-text { color: #9e9e9e; }
.theme-tradicional .section-title {
    text-decoration: underline;
    color: #212121;
}

/* ------------------------------------- */
/* TEMA: MODERNO                         */
/* ------------------------------------- */
.theme-moderno .cv-header {
    text-align: center;
    background-color: #3F51B5;
    color: white;
}
.theme-moderno .header-title { color: #E8EAF6; }
.theme-moderno .header-contact { color: #C5CAE9; }
.theme-moderno .date-text { color: #9e9e9e; }
.theme-moderno .section-title {
    color: #3F51B5;
    border-bottom: 2px solid #3F51B5;
    padding-bottom: 4px;
    text-decoration: none;
}

/* ------------------------------------- */
/* TEMA: CORPORATIVO                     */
/* ------------------------------------- */
.theme-corporativo .cv-header {
    text-align: left;
    background-color: transparent;
    border-bottom: 2px solid #009688; /* Verde esmeralda */
    padding-bottom: 20px !important;
    margin-bottom: 10px;
}
.theme-corporativo .header-name { color: #263238; }
.theme-corporativo .header-title {
    color: #009688;
    text-transform: uppercase;
    font-weight: bold;
    letter-spacing: 1px;
    font-size: 0.9rem !important;
}
.theme-corporativo .header-contact { color: #546E7A; }
.theme-corporativo .date-text { color: #009688; }
.theme-corporativo .cargo-text { color: #263238; }
.theme-corporativo .section-title {
    color: #263238;
    text-transform: uppercase;
    border-left: 4px solid #009688;
    padding-left: 10px;
    font-size: 1.1rem !important;
}

/* Utilidades */
.gap-2 { gap: 8px; }
</style>