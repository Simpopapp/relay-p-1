# Roadmap — s1-site (N=2, pacote site vitrine)

## Fase A — Identidade compartilhada
- [ ] `src/components/site/` com brand/nav/rodapé usados pelas duas rotas.
- Gates: componente único de navegação com Links /, /demo, /ajuda.

## Fase B — Home
- [ ] Hero, 4 passos, duas vias, download final (contrato do prd-s1 §Design).
- [ ] `head()` completo e único para "/".
- Gates: seções todas presentes no código; copy pt-BR sem placeholder.

## Fase C — /ajuda
- [ ] 5 blocos com âncoras (USB debugging, primeira conexão, Discord, problemas, antivírus).
- [ ] `head()` completo e único para "/ajuda".
- Gates: ids de âncora batem com a navegação/sumário.

## Fase D — Revisão de entrega
- [ ] JSX completo, imports resolvíveis (`@/components/site/*`), sem deps novas.
- [ ] RELATORIO.md: decisões, pendências (ex.: URL real de release), arquivos.
- Gates: checklist do aceite do prd-s1 conferido item a item.

## Estado final esperado
Pacote entregue em `/tmp/remix/s1-site/` para integração e verificação (Playwright)
pelo agente principal — o gate final de render é dele.
