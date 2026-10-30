import { createFileRoute } from "@tanstack/react-router";
import { Link } from "@tanstack/react-router";
import { Cable, MonitorSmartphone } from "lucide-react";

export const Route = createFileRoute("/demo")({
  head: () => ({
    meta: [
      { title: "Demo — ApexAudio no celular" },
      {
        name: "description",
        content:
          "Demonstração interativa da tela que roda no Chrome do celular, com áudio simulado.",
      },
      { property: "og:title", content: "Demo — ApexAudio no celular" },
      {
        property: "og:description",
        content:
          "Demonstração interativa da tela que roda no Chrome do celular, com áudio simulado.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: DemoPage,
});

function DemoPage() {
  return (
    <div className="min-h-dvh bg-background text-foreground">
      <div className="mx-auto flex max-w-5xl flex-col items-center gap-10 px-4 py-12 lg:flex-row lg:items-start lg:justify-between">
        <div className="max-w-sm">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-border/80 bg-card/60 px-3 py-1 text-xs font-medium text-muted-foreground">
            <MonitorSmartphone className="size-3.5 text-primary" />
            <span>Demonstração — áudio simulado</span>
          </div>
          <h1 className="font-serif mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
            A tela que roda no{" "}
            <span className="text-primary">Chrome do celular</span>
          </h1>
          <p className="text-muted-foreground mt-4 text-sm leading-relaxed sm:text-base">
            Esta é a mesma página que abre no seu celular via cabo USB. Aqui ela roda
            em modo demonstração: sem cabo, sem celular, com um tom de teste no lugar
            do som do PC. No uso real, o botão Conectar liga o fone do celular ao PC
            e leva sua voz de volta ao microfone virtual.
          </p>
          <p className="text-muted-foreground mt-3 text-sm leading-relaxed">
            Toque em <span className="text-foreground font-medium">Iniciar demo</span> para
            ouvir. O medidor de RTT e a saúde do buffer se comportam como no túnel real.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              to="/ajuda"
              className="inline-flex items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
            >
              <Cable className="mr-2 size-4" />
              Como conectar de verdade
            </Link>
          </div>
        </div>

        <div className="shrink-0">
          <div className="rounded-[2.2rem] border border-border/70 bg-card p-2.5 shadow-2xl shadow-black/40">
            <div className="overflow-hidden rounded-[1.7rem] border border-border/50">
              <iframe
                src="/web/index.html?demo=1"
                title="Demo da página do celular ApexAudio"
                className="h-[640px] w-[320px] border-0 bg-background"
                allow="microphone"
              />
            </div>
          </div>
          <p className="text-muted-foreground mt-3 text-center text-xs">
            Interface real do cliente · modo demonstração
          </p>
        </div>
      </div>
    </div>
  );
}
