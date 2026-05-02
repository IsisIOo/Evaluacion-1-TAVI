import httpClient from "../http-common"

const getCvJson = () => {
  return httpClient.get('/api/cliente/json');
};

export default { getCvJson};