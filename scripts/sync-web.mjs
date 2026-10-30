// Sincroniza o cliente web do celular (apexaudio/web_client) para public/web,
// para que o /demo do site sirva os arquivos estáticos no preview.
// Uso: node scripts/sync-web.mjs
import { cpSync, existsSync, mkdirSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const src = join(root, "apexaudio", "web_client");
const dest = join(root, "public", "web");

if (!existsSync(src)) {
  console.error(`[sync-web] origem ausente: ${src}`);
  process.exit(1);
}

rmSync(dest, { recursive: true, force: true });
mkdirSync(dest, { recursive: true });
const META = ["PRD-s2.md", "ROADMAP-s2.md", "package.json"];
cpSync(src, dest, {
  recursive: true,
  filter: (s) =>
    !s.replaceAll("\\", "/").includes("/tests") &&
    !META.includes(s.split(/[\\/]/).pop()!),
});

console.log(`[sync-web] ${src} -> ${dest}`);
