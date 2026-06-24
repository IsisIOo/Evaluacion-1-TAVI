import httpClient from "../http-common"
import { jwtDecode } from "jwt-decode";

const API_URL = "/api/auth";

const login = async (loginDto) => {
  const params = new URLSearchParams();
  params.append("username", loginDto.email);
  params.append("password", loginDto.password);

  const response = await httpClient.post(`${API_URL}/login`, params, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });

  const token = response.data.access_token;
  if (token) {
    localStorage.setItem("token", token);
    const decoded = jwtDecode(token);
    const user = {
      id: decoded.sub,
      email: loginDto.email,
    };
    localStorage.setItem("user", JSON.stringify(user));
  }
  return response.data;
};

const register = async (registerDto) => {
  const response = await httpClient.post(`${API_URL}/register`, registerDto);
  return response.data;
};

const logout = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
};

const getCurrentUser = () => {
  const user = localStorage.getItem("user");
  return user ? JSON.parse(user) : null;
};

const getToken = () => {
  return localStorage.getItem("token");
};

const isLoggedIn = () => {
  return !!getToken();
};

export default { login, register, logout, getCurrentUser, getToken, isLoggedIn };
