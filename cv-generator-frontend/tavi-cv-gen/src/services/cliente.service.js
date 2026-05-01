import http from '../http-common';

class ClienteService {
  generateCV(data) {
    return http.post('/cv/generate', data);
  }
}

export default new ClienteService();
