import httpClient from "../http-common";

const generateCv = (surveyData) => {
  // Realiza el POST con los datos de la encuesta
  return httpClient.post('/generate', surveyData);
};

export default { generateCv };