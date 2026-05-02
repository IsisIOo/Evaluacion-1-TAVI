import axios from "axios";

// Crea una instancia de Axios
const httpClient = axios.create({
  baseURL: "http://localhost:8000", // URL del backend FastAPI
  headers: {
    "Content-type": "application/json",
  },
});

export default httpClient;
