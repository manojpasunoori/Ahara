import { ApiStatus } from "@/components/api-status";

export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <section className="w-full max-w-xl rounded-3xl border border-[#e3e9e2] bg-white p-10 shadow-sm sm:p-14">
        <p className="mb-8 text-sm font-semibold tracking-[0.2em] text-[#38704f]">AHARA</p>
        <h1 className="text-5xl font-semibold tracking-tight sm:text-6xl">Ahara</h1>
        <p className="mt-5 text-xl leading-8 text-[#667064]">Food that fits your moment.</p>
        <div className="mt-12"><ApiStatus /></div>
      </section>
    </main>
  );
}
