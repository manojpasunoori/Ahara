"use client";

import { useEffect, useState } from "react";
import { getApiHealth } from "@/lib/api";

type Status = "loading" | "connected" | "unavailable";

export function ApiStatus() {
  const [status, setStatus] = useState<Status>("loading");

  useEffect(() => {
    getApiHealth().then(() => setStatus("connected")).catch(() => setStatus("unavailable"));
  }, []);

  const label = status === "connected" ? "API Connected" : status === "unavailable" ? "API Unavailable" : "Checking API";
  return <p aria-live="polite" className="rounded-full border border-[#d8e1d8] bg-white px-4 py-2 text-sm font-medium text-[#405343]">{label}</p>;
}
