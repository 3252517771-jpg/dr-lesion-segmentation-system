import client from "./client";
import type { User, UserCreate, UserListResponse, UserUpdate } from "../types/user";

export async function getUsers(params?: {
  page?: number;
  size?: number;
  search?: string;
  role?: string;
}): Promise<UserListResponse> {
  const response = await client.get<UserListResponse>("/users", { params });
  return response.data;
}

export async function createUser(data: UserCreate): Promise<User> {
  const response = await client.post<{ user: User }>("/users", data);
  return response.data.user;
}

export async function updateUser(id: number, data: UserUpdate): Promise<User> {
  const response = await client.put<{ user: User }>(`/users/${id}`, data);
  return response.data.user;
}

export async function deleteUser(id: number): Promise<void> {
  await client.delete(`/users/${id}`);
}
