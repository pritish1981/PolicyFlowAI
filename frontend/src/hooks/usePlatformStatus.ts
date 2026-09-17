import { useEffect, useState } from "react";
import { getHealth, getReadiness } from "../api/client";
import type { DependencyStatus } from "../api/types";

export type StatusValue = "loading" | "available" | "unavailable" | "error";

interface PlatformStatus {
  backend: StatusValue;
  postgresql: StatusValue;
  redis: StatusValue;
}

const initialStatus: PlatformStatus = {
  backend: "loading",
  postgresql: "loading",
  redis: "loading",
};

function fromDependency(value: DependencyStatus): StatusValue {
  return value === "ready" ? "available" : "unavailable";
}

export function usePlatformStatus(): { status: PlatformStatus; refresh: () => void } {
  const [status, setStatus] = useState<PlatformStatus>(initialStatus);
  const [refreshCount, setRefreshCount] = useState<number>(0);

  useEffect(() => {
    const controller = new AbortController();
    setStatus(initialStatus);

    getHealth(controller.signal)
      .then((response) => {
        setStatus((current) => ({
          ...current,
          backend: response.status === "ok" ? "available" : "unavailable",
        }));
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setStatus((current) => ({ ...current, backend: "error" }));
        }
      });

    getReadiness(controller.signal)
      .then((response) => {
        setStatus((current) => ({
          ...current,
          postgresql: fromDependency(response.components.postgresql),
          redis: fromDependency(response.components.redis),
        }));
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setStatus((current) => ({ ...current, postgresql: "error", redis: "error" }));
        }
      });

    return () => controller.abort();
  }, [refreshCount]);

  return { status, refresh: () => setRefreshCount((count) => count + 1) };
}
