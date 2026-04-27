import axios from "axios";

// Crea una instancia de Axios
const httpClient = axios.create({
  baseURL: "http://localhost:8080", // Cambia esto por la URL de tu backend
  // baseURL: "http://localhost:8081", // Cambia esto por la URL de tu backend
  headers: {
    "Content-type": "application/json",
  },
});

export default httpClient;