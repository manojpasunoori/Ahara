export type ApiHealth = {
  status: "healthy" | "degraded" | "unhealthy";
  service: string;
  version: string;
  database: "healthy" | "unhealthy";
  redis: "healthy" | "unhealthy";
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function getApiHealth(): Promise<ApiHealth> {
  const response = await fetch(`${apiUrl}/api/v1/health`, { cache: "no-store" });
  if (!response.ok) throw new Error(`API health check failed: ${response.status}`);
  return (await response.json()) as ApiHealth;
}
