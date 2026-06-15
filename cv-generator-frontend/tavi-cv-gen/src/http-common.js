import axios from "axios";

// Crea una instancia de Axios
const httpClient = axios.create({
  baseURL: "http://localhost:8000",
  headers: {
    "Content-type": "application/json",
  },
  timeout: 30000,
});

httpClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      error.userMessage = 'La API está tardando demasiado en responder. Por favor, intenta nuevamente.';
    } else if (!error.response) {
      error.userMessage = 'El servidor está caído o tu conexión a internet es inestable. Verifica e intenta nuevamente.';
    } else if (error.response.status === 504) {
      error.userMessage = error.response?.data?.detail || 'La IA generadora está tardando demasiado. Intenta nuevamente.';
    } else if (error.response.status >= 500) {
      error.userMessage = error.response?.data?.detail || 'Error interno del servidor. Por favor, intenta más tarde.';
    } else if (error.response.status === 404) {
      error.userMessage = 'El recurso solicitado no se encontró.';
    } else {
      error.userMessage = error.response?.data?.detail || 'Ha ocurrido un error inesperado.';
    }
    return Promise.reject(error);
  }
);

export default httpClient;
