import { useQuery } from "@tanstack/react-query";

import { getCurrentUser } from "../../api/auth";

export function useCurrentUser() {
  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: getCurrentUser,
    retry: false,
  });
}
