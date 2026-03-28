export interface User {
  id: string;
  email: string;
  fullName: string;
  role: 'admin' | 'doctor' | 'patient';
}

export interface Consultation {
  id: string;
  patientId: string;
  practitionerId: string;
  roomName?: string;
  status: 'scheduled' | 'in_progress' | 'finished' | 'cancelled';
  scheduledAt: string;
  startedAt?: string;
  endedAt?: string;
  durationMinutes: number;
  notes?: string;
}

export interface Transcription {
  id: string;
  consultationId: string;
  text: string;
  language: string;
  confidence: number;
  fhirBundle?: object;
  reviewed: boolean;
  createdAt: string;
}

export interface FHIRBundle {
  resourceType: string;
  type: string;
  total: number;
  entry: Array<{
    resource: object;
  }>;
}
