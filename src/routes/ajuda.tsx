import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/ajuda")({
  head: () => ({
    meta: [
      { title: "Ajuda — ApexAudio" },
      {
        name: "description",
        content: "Guia de instalação e solução de problemas do ApexAudio.",
      },
      { property: "og:title", content: "Ajuda — ApexAudio" },
      {
        property: "og:description",
        content: "Guia de instalação e solução de problemas do ApexAudio.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: AjudaPage,
});

function AjudaPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="font-serif text-3xl font-bold tracking-tight">Ajuda</h1>
      <p className="text-muted-foreground mt-3 text-sm">
        Guia completo em preparação — instale a Depuração USB, conecte o cabo e
        escolha o CABLE Output como microfone.
      </p>
    </div>
  );
}
