import type { ReactNode } from "react";
import { Link } from "@tanstack/react-router";
import { AudioLines, Download, ArrowUpRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export const RELEASE_URL = "https://github.com/apexaudio/apexaudio/releases/latest";

export function DownloadButton() {
  return <Button asChild size="lg" className="h-12 rounded-sm"><a href={RELEASE_URL}><Download aria-hidden="true" />Baixar para Windows</a></Button>;
}

export function SiteShell({ children }: { children: ReactNode }) {
  return <div className="min-h-screen bg-background text-foreground">
    <a href="#conteudo" className="sr-only focus:not-sr-only focus:block focus:p-4 focus:text-primary">Pular para o conteúdo</a>
    <header className="border-b border-border">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-5 py-5 sm:px-8">
        <Link to="/" aria-label="ApexAudio — início" className="flex items-center gap-2 text-xl font-bold tracking-tight"><AudioLines className="size-7 text-primary" aria-hidden="true" />ApexAudio</Link>
        <Badge variant="outline" className="rounded-sm font-mono text-muted-foreground sm:order-last">para Windows</Badge>
        <nav aria-label="Navegação principal" className="flex w-full items-center gap-7 text-sm sm:w-auto">
          {([{ to: "/", label: "Início" }, { to: "/demo", label: "Demo" }, { to: "/ajuda", label: "Ajuda" }] as const).map(item => <Link key={item.to} to={item.to} activeOptions={{ exact: true }} activeProps={{ className: "text-primary", "aria-current": "page" }} className="py-1 text-muted-foreground transition-colors hover:text-foreground">{item.label}</Link>)}
        </nav>
      </div>
    </header>
    <main id="conteudo">{children}</main>
    <footer className="border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col justify-between gap-4 px-5 py-8 text-sm text-muted-foreground sm:flex-row sm:px-8">
        <p><span className="font-semibold text-foreground">ApexAudio</span> · Duas vias. Um cabo.</p>
        <div className="flex gap-6"><Link to="/ajuda" className="hover:text-primary">Precisa de ajuda?</Link><a href={RELEASE_URL} className="inline-flex items-center gap-1 hover:text-primary">Releases<ArrowUpRight className="size-3" aria-hidden="true" /></a></div>
      </div>
    </footer>
  </div>;
}
