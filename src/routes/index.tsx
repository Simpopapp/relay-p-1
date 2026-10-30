import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowDown, ArrowRight, Cable, Headphones, Mic, Monitor, Smartphone } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { SiteShell, DownloadButton } from "@/components/site/site-shell";

export const Route = createFileRoute("/")({
  head: () => ({ meta: [
    { title: "ApexAudio — O áudio do PC, pelo cabo USB" },
    { name: "description", content: "Ouça o PC no fone do celular e use o microfone do Android no computador. Conheça o ApexAudio para Windows, sem Wi-Fi e sem instalar app no celular." },
    { property: "og:title", content: "ApexAudio — Duas vias. Um cabo." },
    { property: "og:description", content: "Áudio do PC no celular e microfone do celular no PC, pelo USB. Veja como conectar em quatro passos." },
    { property: "og:type", content: "website" },
    { name: "twitter:card", content: "summary_large_image" },
  ] }), component: HomePage,
});

const steps = [
  ["Ative a Depuração USB", "No Android, habilite as opções do desenvolvedor e a Depuração USB. É só na primeira vez."],
  ["Execute o ApexAudio.exe", "Baixe no Windows e abra com dois cliques. Para usar o microfone, aceite a instalação opcional do VB-Cable."],
  ["Conecte e toque em Conectar", "Plugue um cabo USB de dados, autorize o computador no celular e toque em Conectar na página que abrir."],
  ["Escolha seu microfone", "No Discord ou jogo, selecione CABLE Output como entrada. A voz do celular chega ao PC."],
];

function HomePage() {
  return <SiteShell>
    <section className="mx-auto grid max-w-6xl gap-12 px-5 py-16 sm:px-8 sm:py-24 lg:grid-cols-[1.25fr_1fr] lg:items-center" aria-labelledby="hero-title">
      <div>
        <Badge variant="outline" className="mb-6 gap-2 rounded-sm font-mono uppercase tracking-widest text-primary"><Cable className="size-3" aria-hidden="true" />Áudio via USB</Badge>
        <h1 id="hero-title" className="max-w-2xl text-4xl font-bold leading-[1.08] tracking-tight sm:text-6xl">O som do PC,<br />no fone do celular<span className="text-primary"> — pelo cabo USB.</span></h1>
        <p className="mt-6 max-w-lg text-lg leading-relaxed text-muted-foreground">Ouça o computador no celular. Leve o microfone do celular para o PC. Sem Wi-Fi, sem app Android e sem complicar.</p>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:flex-wrap"><DownloadButton /><Button asChild variant="outline" size="lg" className="h-12 rounded-sm"><Link to="/demo">Ver demonstração<ArrowRight aria-hidden="true" /></Link></Button></div>
        <p className="mt-4 text-xs text-muted-foreground">Windows 10/11 + Android com Chrome + cabo USB de dados.</p>
      </div>
      <div className="relative border border-border bg-card p-6 sm:p-8" aria-label="Diagrama do áudio em duas direções">
        <div className="mb-10 flex justify-between border-b border-border pb-4 font-mono text-xs uppercase tracking-widest text-muted-foreground"><span>Rota do sinal</span><span className="text-primary">USB / 2 vias</span></div>
        <div className="flex items-center justify-between gap-3"><div className="flex flex-col items-center gap-3"><Monitor className="size-12" strokeWidth={1} aria-hidden="true" /><span className="text-sm">Seu PC</span></div><div className="flex flex-1 flex-col items-center gap-2 text-primary"><span className="font-mono text-xs">áudio →</span><div className="h-px w-full bg-primary" /><span className="font-mono text-xs">← voz</span></div><div className="flex flex-col items-center gap-3"><Smartphone className="size-12" strokeWidth={1} aria-hidden="true" /><span className="text-sm">Seu Android</span></div></div>
        <div className="mt-10 grid grid-cols-2 gap-4 border-t border-border pt-5 text-xs text-muted-foreground"><p><Headphones className="mb-2 size-4 text-primary" aria-hidden="true" />PC → fone do celular</p><p><Mic className="mb-2 size-4 text-primary" aria-hidden="true" />Microfone → PC</p></div>
        <p className="mt-6 font-mono text-xs text-muted-foreground">Conexão local. Sem passar pela nuvem.</p>
      </div>
    </section>
    <section id="como-funciona" className="border-y border-border" aria-labelledby="steps-title"><div className="mx-auto max-w-6xl px-5 py-16 sm:px-8">
      <p className="mb-3 font-mono text-xs uppercase tracking-widest text-primary">01 / Comece aqui</p><h2 id="steps-title" className="text-3xl font-semibold tracking-tight sm:text-4xl">Quatro passos. E o som passa.</h2>
      <ol className="mt-10 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">{steps.map(([title, description], i) => <li key={title} className="border-t border-border pt-5"><span className="font-mono text-3xl text-primary">0{i + 1}</span><h3 className="mt-5 text-lg font-semibold">{title}</h3><p className="mt-3 text-sm leading-relaxed text-muted-foreground">{description}</p></li>)}</ol>
      <Link to="/ajuda" className="mt-8 inline-flex items-center gap-2 text-sm text-primary hover:underline">Ver o guia passo a passo<ArrowRight className="size-4" aria-hidden="true" /></Link>
    </div></section>
    <section className="mx-auto max-w-6xl px-5 py-16 sm:px-8" aria-labelledby="vias-title"><p className="mb-3 font-mono text-xs uppercase tracking-widest text-primary">02 / O caminho do áudio</p><h2 id="vias-title" className="text-3xl font-semibold tracking-tight sm:text-4xl">Um cabo. As duas vias abertas.</h2>
      <div className="mt-10 grid gap-6 md:grid-cols-2"><article className="border border-border bg-card p-7"><Headphones className="mb-6 text-primary" aria-hidden="true" /><h3 className="text-xl font-semibold">Do PC para o seu fone</h3><p className="mt-4 leading-relaxed text-muted-foreground">O ApexAudio captura o som do Windows via WASAPI loopback e envia ao navegador do celular em pequenos blocos de 10 ms. Conecte seu fone ao celular e ouça por lá.</p></article><article className="border border-border bg-card p-7"><Mic className="mb-6 text-primary" aria-hidden="true" /><h3 className="text-xl font-semibold">Da sua voz para o PC</h3><p className="mt-4 leading-relaxed text-muted-foreground">O Chrome captura o microfone do celular com sua permissão. O VB-Cable entrega essa voz aos programas do Windows como uma entrada de microfone.</p></article></div>
      <p className="mt-6 text-sm text-muted-foreground">Tudo pelo túnel USB: sem configurar IP, roteador ou firewall. A latência varia conforme o aparelho; blocos de 10 ms não significam latência total de 10 ms.</p>
    </section>
    <section id="download" className="mx-auto max-w-6xl px-5 pb-16 sm:px-8" aria-labelledby="download-title"><div className="flex flex-col items-start justify-between gap-8 border border-primary/40 bg-primary/5 p-7 md:flex-row md:items-center sm:p-10"><div><ArrowDown className="mb-4 text-primary" aria-hidden="true" /><h2 id="download-title" className="text-3xl font-semibold tracking-tight">Seu próximo áudio começa aqui.</h2><p className="mt-3 max-w-lg text-sm leading-relaxed text-muted-foreground">Windows 10/11, Android com Chrome e um cabo USB de dados. Sem Python, SDK ou compilação. Na página de releases, procure ApexAudio.exe.</p></div><div className="shrink-0"><DownloadButton /><p className="mt-3 text-xs text-muted-foreground">Download pela última release no GitHub.</p></div></div></section>
  </SiteShell>;
}
