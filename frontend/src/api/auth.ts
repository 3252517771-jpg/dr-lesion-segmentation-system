import client from "./client";
import type { User } from "../types/user";

export async function login(username: string, password: string): Promise<User> {
  const response = await client.post<{ user: User }>("/auth/login", { username, password });
  return response.data.user;
}

export async function logout(): Promise<void> {
  await client.post("/auth/logout");
}

export async function getCurrentUser(): Promise<User> {
  const response = await client.get<{ user: User }>("/auth/me");
  return response.data.user;
}
