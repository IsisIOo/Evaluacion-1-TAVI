<template>
    <v-container>
        <div v-if="loading" class="text-center mt-5">
            <v-progress-circular indeterminate color="primary"></v-progress-circular>
            <p class="mt-2">Generando CV</p>
        </div>

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

        <v-alert v-if="!loading && !cvDat" type="error" class="mt-4">
            No se pudieron cargar los datos para generar el CV.
        </v-alert>
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
                            this.cvDat = dLLM.dataLlm.cv_data;
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

            getFormat(){
                if(!this.cvDat){
                    console.warn("No hay datos para hacer el PDF");
                    return;
                }
                

                return {
                    content: [
                        //PERSONAL
                        {
                            text: this.cvDat.personal.nombre_completo,
                            style: 'header'
                        },
                        {
                            text: this.cvDat.personal.profesion,
                            style: 'subHeader'
                        },
                        { 
                            text: `${this.cvDat.personal.email} | ${this.cvDat.personal.telefono} | ${this.cvDat.personal.ciudad}`, 
                            style: 'contact' 
                        },
                        {
                            text: `Rut: ${this.cvDat.personal.rut} | LinkedIn: ${this.cvDat.personal.linkedin}`,
                            style: 'contact', margin: [0, 0, 0, 10]
                        },

                        //PERFIL
                        {
                            text: 'Perfil Profesional',
                            style: 'sectionTitle'
                        },
                        {
                            text: this.cvDat.perfil.propuesta_valor,
                            style: 'bodyText'
                        },
                        {
                            text: `Años de experiencia: ${this.cvDat.perfil.anios_experiencia}`,
                            margin: [0, 5, 0, 10]
                        },
                        {
                            text: `Experticia: ${this.cvDat.perfil.experticia}`,
                            style: 'bodyText'
                        },

                        //EXPERIENCIA
                        {
                            text: 'Experiencia Laboral',
                            style: 'sectionTitle'
                        },
                        ...this.cvDat.experiencias.map(exp => ({
                            stack: [
                                {text: `${exp.cargo} - ${exp.empresa}`, bold: true},
                                {text: `${exp.periodo} | ${exp.pais}`, italics: true, fontSize: 10},
                                {text: `Funciones: ${exp.descripcion}`, margin: [0, 2, 0, 0]},
                                {text: `Logros: ${exp.logros}`, margin: [0, 0, 0, 10]}
                            ],
                            margin: [0, 5, 0, 5]
                        })),

                        //FORMACION
                        {
                            text: 'Formación Académica',
                            style: 'sectionTitle'
                        },
                        ...this.cvDat.formacion.map(form => ({
                            text: `${form.titulo} en ${form.institucion} (${form.periodo})`,
                            margin: [0, 2, 0, 2]
                        })),

                        //HABILIDADES
                        {
                            text: 'Habilidades',
                            style: 'sectionTitle'
                        },
                        {
                            text: this.cvDat.habilidades,
                            style: 'bodyText'
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
                if (!this.cvDat){
                    return;
                }

                const format = this.getFormat();
                pdfMake.createPdf(format).open();
            },


            downloadPDF(){
                if (!this.cvDat){
                    return;
                }

                const format = this.getFormat();
                pdfMake.createPdf(format).download(`CV_ATS_${this.cvDat.personal.nombre_completo}.pdf`);
            }
        },


    }
</script>