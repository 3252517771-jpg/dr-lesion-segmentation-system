import { useQuery } from "@tanstack/react-query";

import { getUsers } from "../../api/users";

export function useUsers(params?: { page?: number; size?: number; search?: string; role?: string }) {
  return useQuery({
    queryKey: ["users", params],
    queryFn: () => getUsers(params),
  });
}
