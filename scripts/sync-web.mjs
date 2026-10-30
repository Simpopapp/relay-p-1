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
cpSync(src, dest, { recursive: true, filter: (s) => !s.includes(`${src}${sep()}tests`) });

function sep() {
  return process.platform === "win32" ? "\\" : "/";
}

console.log(`[sync-web] ${src} -> ${dest}`);
