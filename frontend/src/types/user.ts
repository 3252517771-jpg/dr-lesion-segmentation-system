export type UserRole = "doctor" | "patient";

export interface User {
  id: number;
  username: string;
  display_name: string;
  role: UserRole;
  linked_patient_id: number | null;
  linked_patient_name?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface UserCreate {
  username: string;
  display_name: string;
  password: string;
  role: UserRole;
  linked_patient_id?: number | null;
  is_active?: boolean;
}

export interface UserUpdate {
  username?: string;
  display_name?: string;
  password?: string;
  role?: UserRole;
  linked_patient_id?: number | null;
  is_active?: boolean;
}

export interface UserListResponse {
  users: User[];
  total: number;
  page: number;
  size: number;
}
