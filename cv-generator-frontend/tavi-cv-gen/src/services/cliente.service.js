import httpClient from "../http-common"

const getAll = () => {
  return httpClient.get('/api/cliente/');
};

const getById = id => {
  return httpClient.get(`/api/cliente/${id}`);
};

const getInRadius = (id_tienda_input, radius_km) => {
  return httpClient.get("/api/cliente/inradius", {
    params: { id_tienda_input, radius_km }
  });
};

const update = (id, cliente) => {
  return httpClient.put(`/api/cliente/${id}`, cliente);
};

const deleteCliente = id => {
  return httpClient.delete(`/api/cliente/${id}`);
};

const addDireccion = (id, direccion) => {
  return httpClient.post(`/api/cliente/${id}/direccion`, direccion);
};

const setMainDireccion = (id, direccionId) => {
  return httpClient.put(`/api/cliente/${id}/direccion/${direccionId}/main`);
};

const deleteDireccion = (clienteId, direccionId) => {
  return httpClient.delete(`/api/cliente/${clienteId}/direccion/${direccionId}`);
};



export default { getAll, getById, getInRadius, update, deleteCliente, addDireccion, setMainDireccion, deleteDireccion  };




