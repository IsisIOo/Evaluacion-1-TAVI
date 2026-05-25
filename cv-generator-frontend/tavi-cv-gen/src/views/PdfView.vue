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

        <v-card v-if="pdfUrl">
            <v-card-title>Vista Previa del CV</v-card-title>
            <v-card-text>
                <iframe 
                    :src="pdfUrl" 
                    width="100%" 
                    height="600px" 
                    frameborder="0"
                    type="application/pdf"
                    style="border: none;"
                >
                </iframe>
            </v-card-text>
        </v-card>

        <v-alert v-else-if="!loading && !cvDat" type="error" class="mt-4">
            No se pudieron cargar los datos para generar el CV.
        </v-alert>
    </v-container>
</template>

<script>
    import pdfMake from "pdfmake/build/pdfmake";
    import pdfFonts from "pdfmake/build/vfs_fonts";

    pdfMake.vfs = pdfFonts && pdfFonts.pdfMake ? pdfFonts.pdfMake.vfs : pdfMake.vfs;

    export default{
        name: 'PdfView',
        data () {
            return {
                cvDat: null,
                loading: false,
                pdfUrl: null
            };
        },

        async mounted() {
            await this.getJson();
        },

        methods: {
            async getJson() {
                this.loading = true;
                try {
                    const dLLM = window.history.state;

                    if(dLLM && dLLM.dataLlm){
                        this.cvDat = dLLM.dataLlm.cv_data;
                    }

                    console.log("JSON recibido exitosamente", this.cvDat);
                    //await this.preview();
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


            /* preview() {
                return new Promise((resolve) => {
                    try{
                        const format = this.getFormat();
                        if (!format){
                            return resolve();
                        }

                        const pdfpreview = pdfMake.createPdf(format);
                        
                        //getDataUrl por getBlob
                        pdfpreview.getBlob((blob) => {
                            
                            // URL para el iframe
                            this.pdfUrl = URL.createObjectURL(blob);
                            
                            console.log("PDF URL generada (Blob)");
                            resolve();
                        });
                    } 
                    catch(error){
                        console.error("Error a generar el PDF", error);
                        resolve();
                    }
                    
                });
            },
 */
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

        unmounted() {
            if (this.pdfUrl){
                URL.revokeObjectURL(this.pdfUrl);
            }
        }
    }
</script>