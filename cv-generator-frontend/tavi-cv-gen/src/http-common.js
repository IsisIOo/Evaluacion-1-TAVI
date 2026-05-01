import axios from "axios";

// Crea una instancia de Axios
const httpClient = axios.create({
  baseURL: "http://localhost:8000/api/v1",
  headers: {
    "Content-type": "application/json",
  },
});

export default httpClient;
