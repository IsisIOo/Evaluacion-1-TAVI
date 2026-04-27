import httpClient from "../http-common"
import { jwtDecode } from "jwt-decode";

const login = (loginDto) => {
  return httpClient.post('/auth/login', loginDto)
    .then((response) => {
      // Captura el token del header 'Authorization'
      const token = response.headers['authorization'];
      if (token) {
        // Guardar solo el token en localStorage
        localStorage.setItem('token', `Bearer ${token}`);
        console.log("Token guardado en localStorage:", token);
        const decodedToken = jwtDecode(token);
        console.log("CONTENIDO TOKEN",decodedToken);

        const user = {
          id_cliente: decodedToken.id_cliente,
          username: decodedToken.username,
          direccion: JSON.parse(decodedToken.direccion),
          email: decodedToken.email,
          telefono: decodedToken.telefono,
          direccionPrincipal: null,
        }

        console.log("OBJ LOGGED USER",user);
        // Guardar el usuario en localStorage
        localStorage.setItem('user', JSON.stringify(user));

      } else {
        console.error("No se recibió el token en el header 'Authorization'");
      }
      return response;
    })
    .catch((error) => {
      console.error("Error al hacer login", error);
    });
};

const register = registerDto => {
    return httpClient.post('/auth/register', registerDto);
}

export default {login, register};