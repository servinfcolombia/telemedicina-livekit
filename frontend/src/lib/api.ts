import { fetchApi } from './fetchApi';

export interface Patient {
  id: string;
  name: string;
  birthDate?: string;
  gender?: string;
}

export interface Doctor {
  id: string;
  name: string;
  specialty: string;
}

export interface Consultation {
  id: string;
  patientId: string;
  doctorId: string;
  scheduledAt: string;
  status: 'scheduled' | 'in-progress' | 'completed' | 'cancelled';
  roomSid?: string;
}

export interface Transcription {
  id: string;
  consultationId: string;
  text: string;
  timestamp: string;
}

export const api = {
  auth: {
    login: (email: string, password: string) =>
      fetchApi('/api/v1/auth/login', { method: 'POST', data: { email, password } }),
    register: (data: { email: string; password: string; name: string; role: string }) =>
      fetchApi('/api/v1/auth/register', { method: 'POST', data }),
  },

  patients: {
    list: () => fetchApi<Patient[]>('/fhir/Patient'),
    get: (id: string) => fetchApi<Patient>(`/fhir/Patient/${id}`),
  },

  doctors: {
    list: () => fetchApi<Doctor[]>('/api/v1/doctors'),
    get: (id: string) => fetchApi<Doctor>(`/api/v1/doctors/${id}`),
  },

  consultations: {
    list: () => fetchApi<Consultation[]>('/api/v1/consultations'),
    get: (id: string) => fetchApi<Consultation>(`/api/v1/consultations/${id}`),
    create: (data: Partial<Consultation>) =>
      fetchApi('/api/v1/consultations', { method: 'POST', data }),
    update: (id: string, data: Partial<Consultation>) =>
      fetchApi(`/api/v1/consultations/${id}`, { method: 'PATCH', data }),
  },

  fhir: {
    createEncounter: (data: object) =>
      fetchApi('/fhir/Encounter', { method: 'POST', data }),
    searchObservations: (patientId: string) =>
      fetchApi(`/fhir/Observation?patient=${patientId}`),
  },

  ia: {
    transcribe: (formData: FormData) =>
      fetchApi<{ text: string }>('/api/v1/ia/transcribe', {
        method: 'POST',
      }),
    extractFhir: (text: string) =>
      fetchApi('/api/v1/ia/extract-fhir', { method: 'POST', data: { text } }),
  },
};
