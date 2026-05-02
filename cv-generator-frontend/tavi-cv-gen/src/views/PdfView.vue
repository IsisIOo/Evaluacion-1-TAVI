<template>
    <v-container>
        <v-btn
            v-if = "cvDat"
            color = "success"
            @click = "generatePDF"
            class="mr-2"
        >
        Generar CV en modo PDF
        </v-btn>

        <v-btn
            v-if = "cvDat"
            color = "success"
            @click = "downloadPDF"
            class="mr-2"
        >
            Descargar CV PDF
        </v-btn>

        <v-card v-if="cvDat">
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

        <v-alert v-else type="error" class="mt-4">
            No se pudieron cargar los datos para generar el CV.
        </v-alert>
    </v-container>
</template>

<script>
    //me falta hacer un service que reciba la informacion de la base de datos
    import pdfMake from "pdfmake/build/pdfmake";
    import pdfFonts from "pdfmake/build/vfs_fonts";
    //import PdfService from "@/services/pdf.service";

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
                    //const cvdata = await PdfService.getCvJson();

                    //this.cvDat = cvdata.data;
                    this.cvDat = {
                        nombre: "Mateo",
                        apellido: "Sánchez",
                        telefono: "555-0199",
                        email: "mateo@ejemplo.com",
                        experiencia: [
                            { puesto: "Ingeniero de Software", empresa: "Google" },
                            { puesto: "Pasante", empresa: "Microsoft" }
                        ]
                    };
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
                        {
                            text: `${this.cvDat.nombre} ${this.cvDat.apellido}`, 
                            style: 'header'
                        },
                        {
                            text: `Teléfono: ${this.cvDat.telefono} | Email: ${this.cvDat.email}\n\n`,
                            style: 'contact'
                        },
                        {
                            text: 'Experiencia Laboral',
                            style: 'sectionTitle'
                        },

                        this.cvDat.experiencia ? this.cvDat.experiencia.map(exp => ({
                            text: `${exp.puesto} en ${exp.empresa}`,
                            margin: [0, 5, 0, 5]
                        })) : []
                    ],
                    styles: {
                        header: { fontSize: 22, bold: true, alignment: 'center' },
                        contact: { fontSize: 10, alignment: 'center', color: 'gray' },
                        sectionTitle: { fontSize: 14, bold: true, decoration: 'underline', margin: [0, 10, 0, 5] }
                    }
                };
            },

            generatePDF() {
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
                pdfMake.createPdf(format).download(`CV_ATS_${this.cvDat.nombre}_${this.cvDat.apellido}.pdf`);
            }
        }
    }
</script>