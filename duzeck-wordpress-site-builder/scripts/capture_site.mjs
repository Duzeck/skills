#!/usr/bin/env node
/**
 * Executor Playwright usado por scripts/capture_site.py (nao chame direto,
 * a nao ser para depurar). Recebe um JSON de configuracao:
 *
 *   { "base": "http://localhost/slug/", "out": "<dir>",
 *     "pages": [{"id": "home", "path": "/", "carousels": {"home_banner": {...}}}],
 *     "viewports": [{"name": "desktop", "width": 1440, "height": 900}],
 *     "axe": true, "checkLinks": true, "maxLinks": 200, "stickyHeader": false }
 *
 * Para cada pagina x viewport: captura full-page, erros de console e de
 * JS, respostas HTTP >= 400, imagens quebradas e rolagem horizontal. Axe
 * (WCAG 2 A/AA) roda em desktop e mobile; links internos sao checados uma
 * vez. Escreve <out>/report.json.
 *
 * Playwright e axe-core sao resolvidos da instalacao GLOBAL do npm
 * (npm i -g playwright axe-core && playwright install chromium).
 */
import { execSync } from "node:child_process";
import { createRequire } from "node:module";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

const npmRoot = process.env.NPM_GLOBAL_ROOT || execSync("npm root -g").toString().trim();
const requireGlobal = createRequire(join(npmRoot, "noop.js"));
const { chromium } = requireGlobal("playwright");
const axePath = requireGlobal.resolve("axe-core/axe.min.js");

const config = JSON.parse(readFileSync(process.argv[2], "utf-8"));
mkdirSync(config.out, { recursive: true });

const FREEZE_CSS = `*,*::before,*::after{animation-duration:0s!important;animation-delay:0s!important;transition-duration:0s!important;transition-delay:0s!important;caret-color:transparent!important}`;
const AXE_VIEWPORTS = new Set(["desktop", "mobile"]);

function pageUrl(path) {
  return new URL(path.replace(/^\//, ""), config.base.endsWith("/") ? config.base : config.base + "/").href;
}

async function autoScroll(page) {
  // Dispara lazy-load e animacoes de entrada antes da captura full-page.
  await page.evaluate(async () => {
    const step = Math.max(200, Math.floor(window.innerHeight * 0.8));
    for (let y = 0; y < document.documentElement.scrollHeight; y += step) {
      window.scrollTo(0, y);
      await new Promise((r) => setTimeout(r, 80));
    }
    window.scrollTo(0, 0);
  });
  await page.waitForTimeout(300);
}

async function inspect(page) {
  return page.evaluate(() => {
    const vw = window.innerWidth;
    const describe = (el) => {
      let s = el.tagName.toLowerCase();
      if (el.id) s += "#" + el.id;
      if (el.classList.length) s += "." + [...el.classList].slice(0, 2).join(".");
      return s;
    };
    const offenders = [];
    for (const el of document.body.querySelectorAll("*")) {
      const r = el.getBoundingClientRect();
      if (r.width && r.right > vw + 1) {
        offenders.push(`${describe(el)} (right=${Math.round(r.right)}px)`);
        if (offenders.length >= 5) break;
      }
    }
    const brokenImages = [...document.images]
      .filter((img) => img.complete && img.naturalWidth === 0 && img.getAttribute("src"))
      .map((img) => img.currentSrc || img.src);
    // Links sem destino: href ausente, vazio ou "#". Nao geram 404 (apontam
    // para a propria pagina), por isso a checagem de links quebrados nao os ve.
    // Em menu/cabecalho sao defeito; em outros lugares, provisorio a registrar.
    const emptyLinks = [...document.querySelectorAll("a")]
      .filter((a) => { const h = (a.getAttribute("href") || "").trim(); return h === "" || h === "#"; })
      .map((a) => ({
        text: (a.innerText || a.getAttribute("aria-label") || "").trim().slice(0, 60),
        inNav: !!a.closest("nav, header"),
      }));
    const links = [...document.querySelectorAll("a[href]")]
      .map((a) => a.href.split("#")[0])
      .filter((h) => h.startsWith(location.origin));
    return {
      scrollWidth: document.documentElement.scrollWidth,
      viewportWidth: vw,
      horizontalOverflow: document.documentElement.scrollWidth > vw + 1,
      overflowOffenders: offenders,
      brokenImages,
      emptyLinks,
      links: [...new Set(links)],
      title: document.title,
      // innerText ja aplica text-transform (ex.: eyebrow em caixa alta);
      // a comparacao com o inventario copy e feita sem diferenciar caixa.
      // + placeholders e rotulos de botoes <input> (formularios), que nao
      // aparecem no innerText mas sao texto visivel da referencia.
      text: [
        document.body.innerText,
        ...[...document.querySelectorAll(
          "input[placeholder], textarea[placeholder], input[type=submit], input[type=button]"
        )].map((el) => el.getAttribute("placeholder") || el.value || ""),
      ].join(String.fromCharCode(10)).slice(0, 200000),
    };
  });
}

// Navegacao (references/navigation.md): header sticky continua visivel ao
// rolar; toda ancora do menu existe; o destino nao fica atras do header.
// Roda DEPOIS da captura (rola a pagina e mexe no scroll-spy).
async function checkNavigation(page, sticky) {
  return page.evaluate(async (sticky) => {
    const wait = (ms) => new Promise((r) => setTimeout(r, ms));
    const header = document.querySelector("[data-site-header]") || document.querySelector("body > header, header");
    if (!header) return { headerFound: false, stickyFailures: sticky ? ["header nao encontrado"] : [], missingAnchors: [], obscuredAnchors: [] };
    const res = { headerFound: true, stickyFailures: [], missingAnchors: [], obscuredAnchors: [] };
    const maxY = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
    if (sticky && maxY > 0) {
      for (const [label, y] of [["meio", maxY / 2], ["fim", maxY]]) {
        window.scrollTo(0, y);
        await wait(150);
        const r = header.getBoundingClientRect();
        const st = getComputedStyle(header);
        const visible = r.height > 0 && r.top >= -1 && r.top <= 50 && st.visibility !== "hidden" && st.display !== "none";
        if (!visible) res.stickyFailures.push(`${label} da pagina (top do header=${Math.round(r.top)}px)`);
      }
    }
    const here = location.origin + location.pathname;
    const seen = new Set();
    for (const a of document.querySelectorAll("header a[href*='#'], nav a[href*='#']")) {
      const url = new URL(a.href, location.href);
      if (url.hash.length < 2 || url.origin + url.pathname !== here || seen.has(url.hash)) continue;
      seen.add(url.hash);
      const label = ((a.textContent || a.getAttribute("aria-label") || "").trim().slice(0, 40)) || url.hash;
      const target = document.getElementById(decodeURIComponent(url.hash.slice(1)));
      if (!target) { res.missingAnchors.push(`${label} -> ${url.hash}`); continue; }
      target.scrollIntoView({ block: "start", behavior: "instant" });
      await wait(150);
      const headerBottom = header.getBoundingClientRect().bottom;
      const top = target.getBoundingClientRect().top;
      if (top < headerBottom - 2) res.obscuredAnchors.push(`${label} -> ${url.hash} (${Math.round(headerBottom - top)}px sob o header)`);
    }
    window.scrollTo(0, 0);
    return res;
  }, sticky);
}

// Carrosseis (references/carousels.md): cada carousels[] do Blueprint
// existe na pagina, com o numero de slides, os controles e o autoplay
// declarados; setas funcionam; autoplay tem pausa e NAO gira com
// prefers-reduced-motion (o contexto de captura usa reduce, entao a captura
// mostra sempre o slide 1, comparavel com a referencia).
async function checkCarousels(page, expected) {
  return page.evaluate(async (expected) => {
    const wait = (ms) => new Promise((r) => setTimeout(r, ms));
    const out = [];
    const found = new Set();
    for (const root of document.querySelectorAll("[data-carousel]")) {
      const id = root.dataset.carousel || "(sem id)";
      found.add(id);
      const exp = expected ? expected[id] : null;
      const issues = [];
      const slides = root.querySelectorAll("[data-carousel-slide]").length;
      const autoplay = root.dataset.autoplay === "true";
      const controls = (exp && exp.controls) || {};
      if (expected && !exp) issues.push("nao esta em carousels[] do Blueprint");
      if (slides < 2) issues.push(`${slides} slide(s) - carrossel precisa de 2 ou mais`);
      if (exp && Number.isInteger(exp.slide_count) && slides !== exp.slide_count) issues.push(`${slides} slide(s), Blueprint diz ${exp.slide_count}`);
      if (!root.classList.contains("carousel--js")) issues.push("JS do carrossel nao inicializou (carousel.js enfileirado?)");
      if (exp && typeof exp.autoplay === "boolean" && exp.autoplay !== autoplay) issues.push(`autoplay ${autoplay}, Blueprint diz ${exp.autoplay}`);
      if (autoplay && !root.querySelector("[data-carousel-toggle]")) issues.push("autoplay sem botao de pausa (WCAG 2.2.2)");
      if (autoplay && root.dataset.playing === "true" && matchMedia("(prefers-reduced-motion: reduce)").matches) issues.push("gira mesmo com prefers-reduced-motion");
      const next = root.querySelector("[data-carousel-next]");
      if (controls.arrows && !next) issues.push("Blueprint pede setas e nao ha");
      const dots = root.querySelectorAll("[data-carousel-dot]").length;
      if (controls.dots && !dots) issues.push("Blueprint pede bolinhas e nao ha");
      if (next && !next.disabled) {
        const before = root.dataset.index;
        next.click();
        await wait(400);
        if (root.dataset.index === before) issues.push("seta 'proximo' nao avanca");
        root.querySelector("[data-carousel-prev]")?.click();
        await wait(400);
      }
      out.push({ id, slides, dots, autoplay, issues });
    }
    for (const id of Object.keys(expected || {})) {
      if (!found.has(id)) out.push({ id, slides: 0, dots: 0, autoplay: false, issues: ["ausente na pagina (data-carousel nao encontrado)"] });
    }
    return out;
  }, expected);
}

// Formularios (references/forms.md): cada forms[] do Blueprint esta na
// pagina com os campos, tipos, rotulo acessivel, obrigatoriedade,
// placeholder e texto do botao LITERAIS. Com submit=true preenche com dados
// de teste, envia e le o status do CF7 (data-status do <form>).
const CF7_FINAL = ["sent", "failed", "invalid", "spam", "unaccepted", "aborted", "payment_required"];
const QA_VALUES = { text: "Teste QA", textarea: "Mensagem de teste do QA automatico.", email: "qa@example.com",
  tel: "(11) 99999-9999", url: "https://example.com", number: "1", date: "2030-01-15" };

async function checkForms(page, expected, submit) {
  if (!expected) return [];
  const out = [];
  for (const [fid, exp] of Object.entries(expected)) {
    const r = { id: fid, issues: [], status: null, response: null };
    const info = await page.evaluate((exp) => {
      const sel = (n) => `[name="${n}"], [name="${n}[]"]`;
      const first = (exp.fields || [])[0];
      const anchor = first && document.querySelector(sel(first.name));
      const form = anchor && anchor.closest("form");
      if (!form) return { found: false };
      form.setAttribute("data-qa-form", exp.id);
      const issues = [];
      for (const f of exp.fields || []) {
        const input = form.querySelector(sel(f.name));
        if (!input) { issues.push(`campo ${f.name} ausente`); continue; }
        const group = f.type === "checkbox" || f.type === "radio";
        if (f.required && !group && input.getAttribute("aria-required") !== "true" && !input.required) issues.push(`campo ${f.name} obrigatorio sem aria-required`);
        const simple = !["select", "textarea", "checkbox", "radio"].includes(f.type);
        if (simple && input.type !== f.type) issues.push(`campo ${f.name} type=${input.type} (Blueprint: ${f.type})`);
        if (f.placeholder && f.type !== "select" && (input.getAttribute("placeholder") || "").trim() !== String(f.placeholder).trim()) issues.push(`placeholder de ${f.name} "${input.getAttribute("placeholder") || ""}" (referencia: "${f.placeholder}")`);
        const labelled = (input.labels && input.labels.length) || input.getAttribute("aria-label") || input.getAttribute("aria-labelledby") || (group && input.closest("fieldset")?.querySelector("legend"));
        if (!labelled) issues.push(`campo ${f.name} sem rotulo acessivel`);
      }
      const btn = form.querySelector("button[type=submit], input[type=submit]");
      const text = btn ? (btn.innerText || btn.value || "").replace(/\s+/g, " ").trim() : "";
      if (!btn) issues.push("sem botao de envio");
      else if (exp.submit_label && text !== String(exp.submit_label).trim()) issues.push(`botao "${text}" (referencia: "${exp.submit_label}")`);
      return { found: true, issues };
    }, { ...exp, id: fid });
    if (!info.found) { r.issues.push("ausente na pagina (nenhum campo do Blueprint encontrado)"); out.push(r); continue; }
    r.issues.push(...info.issues);

    if (submit && !info.issues.some((i) => i.endsWith("ausente"))) {
      const form = page.locator(`form[data-qa-form="${fid}"]`);
      let skip = null;
      for (const f of exp.fields || []) {
        const field = form.locator(`[name="${f.name}"], [name="${f.name}[]"]`).first();
        if (f.type === "select") await field.selectOption({ index: 1 }).catch(() => {});
        else if (f.type === "checkbox" || f.type === "radio") await field.check().catch(() => {});
        else if (f.type === "file") { if (f.required) skip = `campo de arquivo obrigatorio (${f.name}) - envio testado so manualmente`; }
        else await field.fill(QA_VALUES[f.type] || QA_VALUES.text).catch(() => {});
      }
      for (const box of await form.locator(".wpcf7-acceptance input[type=checkbox]").all()) await box.check().catch(() => {});
      if (skip) r.issues.push(skip);
      else {
        await form.locator("button[type=submit], input[type=submit]").first().click();
        try {
          await page.waitForFunction(([id, done]) => done.includes(document.querySelector(`form[data-qa-form="${id}"]`)?.dataset.status), [fid, CF7_FINAL], { timeout: 20000 });
        } catch { /* status fica como esta */ }
        const res = await form.evaluate((f) => ({ status: f.dataset.status || null, response: (f.querySelector(".wpcf7-response-output")?.textContent || "").trim() }));
        r.status = res.status;
        r.response = res.response;
        if (res.status !== "sent") r.issues.push(`envio nao concluido: status ${res.status || "?"} - "${res.response}"`);
      }
    }
    out.push(r);
  }
  return out;
}

// Mapas (references/maps.md): presente, iframe so depois do clique (load
// click), clique carrega o mapa com title, link "Como chegar" valido.
async function checkMaps(page, expected) {
  if (!expected) return [];
  const out = [];
  for (const [mid, exp] of Object.entries(expected)) {
    const r = { id: mid, issues: [] };
    const root = page.locator(`[data-map="${mid}"]`);
    if (!(await root.count())) { r.issues.push("ausente na pagina (data-map nao encontrado)"); out.push(r); continue; }
    const before = await root.evaluate((el) => ({
      iframe: !!el.querySelector("iframe"),
      trigger: el.querySelector("[data-map-load]")?.getAttribute("href") || null,
      directions: el.querySelector("[data-map-directions]")?.getAttribute("href") || null,
    }));
    if (exp.directions_link && !(before.directions && /destination=|mlat=/.test(before.directions))) r.issues.push("link 'Como chegar' ausente ou sem destino");
    if ((exp.load || "click") === "click") {
      if (before.iframe) r.issues.push("iframe do mapa carregado antes do clique (LGPD/desempenho)");
      if (!before.trigger) r.issues.push("sem botao 'Carregar mapa'");
      else {
        await root.locator("[data-map-load]").first().click();
        await page.waitForTimeout(500);
        const after = await root.evaluate((el) => { const f = el.querySelector("iframe"); return f ? { src: f.src, title: f.title } : null; });
        if (!after) r.issues.push("clicar em 'Carregar mapa' nao carrega o mapa (map.js enfileirado?)");
        else if (!after.title) r.issues.push("iframe do mapa sem title");
      }
    }
    out.push(r);
  }
  return out;
}

// Galerias (references/galleries.md): quantidade visivel/total, texto
// alternativo e, com lightbox, abrir / navegar / Esc / foco devolvido.
async function checkGalleries(page, expected) {
  if (!expected) return [];
  const out = [];
  for (const [gid, exp] of Object.entries(expected)) {
    const r = { id: gid, issues: [] };
    const root = page.locator(`[data-gallery="${gid}"]`);
    if (!(await root.count())) { r.issues.push("ausente na pagina (data-gallery nao encontrado)"); out.push(r); continue; }
    const info = await root.evaluate((el) => {
      const items = [...el.querySelectorAll(".gallery__item")];
      const shown = items.filter((li) => !li.hidden);
      return {
        total: items.length,
        visible: shown.length,
        noAlt: shown.filter((li) => !(li.querySelector("img")?.getAttribute("alt") || "").trim()).length,
        links: el.querySelectorAll("[data-gallery-item]").length,
      };
    });
    if (Number.isInteger(exp.visible_count) && info.visible !== exp.visible_count) r.issues.push(`${info.visible} foto(s) visivel(is), referencia mostra ${exp.visible_count}`);
    const total = Number.isInteger(exp.total_count) ? exp.total_count : exp.visible_count;
    if (Number.isInteger(total) && info.total !== total) r.issues.push(`${info.total} foto(s) no total, Blueprint diz ${total}`);
    if (info.noAlt) r.issues.push(`${info.noAlt} foto(s) sem texto alternativo (preencha na Biblioteca de Midia)`);
    if (exp.lightbox === false && info.links) r.issues.push("Blueprint diz sem lightbox, mas as fotos sao links");
    if (exp.lightbox) {
      if (!info.links) r.issues.push("Blueprint pede lightbox e as fotos nao sao clicaveis");
      else {
        const first = root.locator("[data-gallery-item]").first();
        await first.click();
        await page.waitForTimeout(300);
        const opened = await page.evaluate(() => {
          const d = document.querySelector("dialog.lightbox[open]");
          return d ? { counter: d.querySelector(".lightbox__counter")?.textContent || "", img: !!d.querySelector(".lightbox__img")?.getAttribute("src"), label: d.getAttribute("aria-label") } : null;
        });
        if (!opened) r.issues.push("clicar na foto nao abre o lightbox (gallery.js enfileirado?)");
        else {
          if (!opened.img) r.issues.push("lightbox abre sem a foto");
          if (info.links > 1) {
            await page.keyboard.press("ArrowRight");
            await page.waitForTimeout(150);
            const idx = await page.evaluate(() => document.querySelector("dialog.lightbox[open]")?.dataset.index);
            if (idx !== "1") r.issues.push("seta direita nao avanca a foto no lightbox");
          }
          await page.keyboard.press("Escape");
          await page.waitForTimeout(200);
          const after = await page.evaluate((gid) => ({
            open: !!document.querySelector("dialog.lightbox[open]"),
            focusBack: document.activeElement === document.querySelector(`[data-gallery="${gid}"] [data-gallery-item]`),
          }), gid);
          if (after.open) r.issues.push("Esc nao fecha o lightbox");
          else if (!after.focusBack) r.issues.push("ao fechar, o foco nao volta para a foto clicada");
        }
      }
    }
    out.push(r);
  }
  return out;
}

// Videos (references/videos.md): embed so no clique e sem cookies (nocookie/
// dnt); arquivo com controles/capa/legenda; fundo nao toca com movimento
// reduzido, tem pausa e nao baixa no celular.
async function checkVideos(page, expected, viewport) {
  if (!expected) return [];
  const out = [];
  for (const [vid, exp] of Object.entries(expected)) {
    const r = { id: vid, issues: [] };
    const root = page.locator(`[data-video="${vid}"]`);
    if (!(await root.count())) { r.issues.push("ausente na pagina (data-video nao encontrado)"); out.push(r); continue; }
    const kind = await root.getAttribute("data-video-kind");
    if (exp.kind && kind !== exp.kind) r.issues.push(`kind ${kind}, Blueprint diz ${exp.kind}`);
    if (kind === "embed") {
      const before = await root.evaluate((el) => {
        const t = el.querySelector("[data-video-load]");
        return { iframe: !!el.querySelector("iframe"), src: t?.getAttribute("data-video-src") || "", name: (t?.textContent || "").replace(/\s+/g, " ").trim() };
      });
      if (before.iframe) r.issues.push("player carregado antes do clique (LGPD/desempenho)");
      if (!before.src) r.issues.push("sem botao play / URL do video");
      else {
        if (!/youtube-nocookie\.com|player\.vimeo\.com\/.*dnt=1/.test(before.src)) r.issues.push("embed sem modo de privacidade (youtube-nocookie / dnt=1)");
        if (!before.name) r.issues.push("botao play sem nome acessivel");
        await root.locator("[data-video-load]").first().click();
        await page.waitForTimeout(400);
        const iframe = await root.evaluate((el) => { const f = el.querySelector("iframe"); return f ? { title: f.title } : null; });
        if (!iframe) r.issues.push("clicar no play nao carrega o player (video.js enfileirado?)");
        else if (!iframe.title) r.issues.push("player sem title");
      }
    } else if (kind === "file") {
      const info = await root.evaluate((el) => {
        const v = el.querySelector("video");
        return v ? { controls: v.controls, poster: !!v.getAttribute("poster"), sources: v.querySelectorAll("source").length, track: !!v.querySelector("track[kind=captions]"), autoplay: v.autoplay } : null;
      });
      if (!info) r.issues.push("sem elemento <video>");
      else {
        if (!info.controls) r.issues.push("video sem controles");
        if (info.autoplay) r.issues.push("video com som em autoplay");
        if (!info.poster) r.issues.push("video sem capa (poster)");
        if (!info.sources) r.issues.push("video sem arquivo");
        if (exp.captions && !info.track) r.issues.push("Blueprint pede legenda e nao ha <track kind=captions>");
      }
    } else if (kind === "background") {
      const info = await root.evaluate((el) => {
        const v = el.querySelector("video");
        return { playing: el.dataset.playing === "true" || (v ? !v.paused : false), hidden: v?.getAttribute("aria-hidden"), src: v?.currentSrc || "", toggle: !!el.querySelector("[data-video-toggle]"), toggleHidden: el.querySelector("[data-video-toggle]")?.hidden, reduce: matchMedia("(prefers-reduced-motion: reduce)").matches };
      });
      if (info.reduce && info.playing) r.issues.push("video de fundo toca mesmo com prefers-reduced-motion");
      if (info.hidden !== "true") r.issues.push("video de fundo sem aria-hidden (e decorativo)");
      if (!info.toggle) r.issues.push("video de fundo sem botao de pausa (WCAG 2.2.2)");
      if (viewport === "mobile" && info.src) r.issues.push("video de fundo baixado no celular (devia ficar so a capa)");
      if (viewport === "desktop" && info.toggle && info.toggleHidden) r.issues.push("botao de pausa/play invisivel no desktop");
    }
    out.push(r);
  }
  return out;
}

// Acordeoes/FAQ e abas (references/disclosures.md). Rodam por ultimo: o
// teste de link direto recarrega a pagina com #id.
async function checkAccordions(page, expected, viewport) {
  if (!expected) return [];
  const out = [];
  const base = page.url().split("#")[0];
  for (const [aid, exp] of Object.entries(expected)) {
    const r = { id: aid, issues: [] };
    const sel = `[data-accordion="${aid}"]`;
    if (!(await page.locator(sel).count())) { r.issues.push("ausente na pagina (data-accordion nao encontrado)"); out.push(r); continue; }
    const info = await page.evaluate((sel) => {
      const items = [...document.querySelectorAll(`${sel} > details`)];
      return {
        count: items.length,
        open: items.map((d, i) => (d.open ? i + 1 : 0)).filter(Boolean),
        empty: items.filter((d) => !(d.querySelector(".accordion__panel")?.textContent || "").trim()).length,
        noSummary: items.filter((d) => !d.querySelector(":scope > summary")).length,
        titles: items.map((d) => (d.querySelector("summary")?.textContent || "").replace(/\s+/g, " ").trim()),
        ids: items.map((d) => d.id),
      };
    }, sel);
    if (Number.isInteger(exp.item_count) && info.count !== exp.item_count) r.issues.push(`${info.count} item(ns), referencia mostra ${exp.item_count}`);
    if (Array.isArray(exp.open_in_reference) && info.open.join(",") !== exp.open_in_reference.join(",")) r.issues.push(`abertos ao carregar: [${info.open}] (referencia: [${exp.open_in_reference}])`);
    if (info.empty) r.issues.push(`${info.empty} item(ns) sem conteudo`);
    if (info.noSummary) r.issues.push(`${info.noSummary} item(ns) sem <summary>`);
    if (info.count >= 2 && typeof exp.exclusive === "boolean") {
      await page.evaluate((sel) => { const d = document.querySelectorAll(`${sel} > details`); d.forEach((x) => (x.open = false)); d[0].open = true; }, sel);
      await page.locator(`${sel} > details >> nth=1`).locator("summary").click();
      await page.waitForTimeout(150);
      const openNow = await page.evaluate((sel) => document.querySelectorAll(`${sel} > details[open]`).length, sel);
      if (exp.exclusive && openNow !== 1) r.issues.push(`abrir um item deixou ${openNow} abertos (Blueprint: um por vez)`);
      if (!exp.exclusive && openNow < 2) r.issues.push("abrir um item fechou o outro (Blueprint: varios abertos)");
    }
    if (exp.faq && exp.structured_data !== false) {
      const names = await page.evaluate(() => [...document.querySelectorAll('script[type="application/ld+json"]')]
        .flatMap((s) => { try { const d = JSON.parse(s.textContent); return (Array.isArray(d) ? d : [d]).filter((x) => x["@type"] === "FAQPage").flatMap((x) => (x.mainEntity || []).map((q) => q.name)); } catch { return []; } }));
      if (!names.length) r.issues.push("FAQ sem dados estruturados FAQPage (JSON-LD)");
      else {
        const missing = info.titles.filter((t) => !names.includes(t));
        if (missing.length) r.issues.push(`${missing.length} pergunta(s) fora do JSON-LD: ${missing.slice(0, 2).join(" | ")}`);
      }
    }
    if (viewport === "desktop" && info.count >= 2) {
      const target = info.ids[info.count - 1];
      if (!target) r.issues.push("itens sem id - link direto impossivel");
      else {
        await page.goto(`${base}#${target}`, { waitUntil: "networkidle" });
        await page.waitForTimeout(300);
        const deep = await page.evaluate((id) => { const d = document.getElementById(id); const t = d.getBoundingClientRect().top; return { open: d.open, visible: t >= 0 && t < innerHeight }; }, target);
        if (!deep.open) r.issues.push(`link direto #${target} nao abre o item`);
        else if (!deep.visible) r.issues.push(`link direto #${target} nao rola ate o item`);
      }
    }
    out.push(r);
  }
  return out;
}

async function checkTabs(page, expected, viewport) {
  if (!expected) return [];
  const out = [];
  const base = page.url().split("#")[0];
  for (const [tid, exp] of Object.entries(expected)) {
    const r = { id: tid, issues: [] };
    const sel = `[data-tabs="${tid}"]`;
    if (!(await page.locator(sel).count())) { r.issues.push("ausente na pagina (data-tabs nao encontrado)"); out.push(r); continue; }
    const state = () => page.evaluate((sel) => {
      const root = document.querySelector(sel);
      const list = root.querySelector("[data-tabs-list]");
      const tabs = [...root.querySelectorAll("[data-tabs-tab]")];
      const panels = [...root.querySelectorAll("[data-tabs-panel]")];
      return {
        count: tabs.length,
        listVisible: !!list && !list.hidden && list.getAttribute("role") === "tablist",
        selected: tabs.map((t, i) => (t.getAttribute("aria-selected") === "true" ? i + 1 : 0)).filter(Boolean),
        visiblePanels: panels.filter((p) => !p.hidden && p.offsetParent !== null).length,
        empty: panels.filter((p) => !p.textContent.replace(p.querySelector(".tabs__panel-title")?.textContent || "", "").trim()).length,
        focused: tabs.indexOf(document.activeElement) + 1,
        ids: panels.map((p) => p.id),
      };
    }, sel);
    let s = await state();
    if (Number.isInteger(exp.tab_count) && s.count !== exp.tab_count) r.issues.push(`${s.count} aba(s), referencia mostra ${exp.tab_count}`);
    if (s.empty) r.issues.push(`${s.empty} painel(is) sem conteudo`);
    const stacked = exp.mobile === "stack" && viewport === "mobile";
    if (stacked) {
      if (s.listVisible) r.issues.push("mobile stack: as abas deviam sumir no celular");
      if (s.visiblePanels !== s.count) r.issues.push(`mobile stack: ${s.visiblePanels} de ${s.count} painel(is) visivel(is)`);
    } else {
      if (!s.listVisible) r.issues.push("abas nao inicializaram (role=tablist ausente - disclosure.js enfileirado?)");
      else {
        if (s.selected.length !== 1 || (Number.isInteger(exp.active_in_reference) && s.selected[0] !== exp.active_in_reference)) r.issues.push(`aba ativa [${s.selected}] (referencia: ${exp.active_in_reference})`);
        if (s.visiblePanels !== 1) r.issues.push(`${s.visiblePanels} painel(is) visivel(is) - devia ser 1`);
        await page.locator(`${sel} [data-tabs-tab][aria-selected="true"]`).focus();
        await page.keyboard.press("End");
        s = await state();
        if (s.selected[0] !== s.count || s.focused !== s.count) r.issues.push("tecla End nao leva a ultima aba");
        await page.keyboard.press("ArrowRight");
        s = await state();
        if (s.selected[0] !== 1 || s.focused !== 1) r.issues.push("seta direita na ultima aba nao volta a primeira");
        if (viewport === "desktop" && s.count >= 2) {
          const target = s.ids[s.count - 1];
          if (!target) r.issues.push("paineis sem id - link direto impossivel");
          else {
            await page.goto(`${base}#${target}`, { waitUntil: "networkidle" });
            await page.waitForTimeout(300);
            const deep = await state();
            if (deep.selected[0] !== deep.count) r.issues.push(`link direto #${target} nao seleciona a aba`);
          }
        }
      }
    }
    out.push(r);
  }
  return out;
}

// Tabelas e precos (references/tables-pricing.md).
const BRL = /^(.*\s)?R\$ \d{1,3}(\.\d{3})*(,\d{2})?(\s.*)?$/;

async function checkTables(page, expected, viewport) {
  if (!expected) return [];
  const out = [];
  for (const [tid, exp] of Object.entries(expected)) {
    const r = { id: tid, issues: [] };
    const sel = `[data-table="${tid}"]`;
    if (!(await page.locator(sel).count())) { r.issues.push("ausente na pagina (data-table nao encontrado)"); out.push(r); continue; }
    const info = await page.evaluate(([sel, cards]) => {
      const root = document.querySelector(sel);
      const table = root.querySelector("table");
      const region = root.querySelector(".data-table__scroll");
      const heads = [...table.querySelectorAll("thead th")];
      const rows = [...table.querySelectorAll("tbody tr")];
      const cells = rows.flatMap((tr) => [...tr.children]);
      const thead = table.querySelector("thead").getBoundingClientRect();
      return {
        caption: (table.querySelector("caption")?.textContent || "").trim(),
        headers: heads.map((th) => th.textContent.trim()),
        scoped: heads.filter((th) => th.getAttribute("scope") === "col").length,
        rows: rows.length,
        empty: cells.filter((c) => !c.textContent.trim()).length,
        checkNoText: cells.filter((c) => c.querySelector(".data-table__check") && !c.querySelector(".screen-reader-text")?.textContent.trim()).length,
        region: !!region && region.getAttribute("role") === "region" && region.hasAttribute("tabindex") && !!region.getAttribute("aria-labelledby"),
        cardsOk: cards ? thead.height <= 1 && getComputedStyle(rows[0]).display === "block" && cells.every((c) => ["cell", "rowheader"].includes(c.getAttribute("role"))) : true,
      };
    }, [sel, exp.mobile === "cards" && viewport === "mobile"]);
    if (!info.caption) r.issues.push("tabela sem <caption> (nome para leitor de tela)");
    const labels = (exp.columns || []).map((c) => c.label);
    if (labels.length && info.headers.join("|") !== labels.join("|")) r.issues.push(`cabecalhos [${info.headers.join(", ")}] (referencia: [${labels.join(", ")}])`);
    if (info.scoped !== info.headers.length) r.issues.push("cabecalho sem scope=col");
    if (Number.isInteger(exp.row_count) && info.rows !== exp.row_count) r.issues.push(`${info.rows} linha(s), referencia mostra ${exp.row_count}`);
    if (info.empty) r.issues.push(`${info.empty} celula(s) vazia(s)`);
    if (info.checkNoText) r.issues.push(`${info.checkNoText} ✓/✗ sem texto para leitor de tela`);
    if (!info.region) r.issues.push("tabela fora de regiao rolavel nomeada e focavel (teclado nao rola no celular)");
    if (!info.cardsOk) r.issues.push("mobile cards: linhas nao viraram cards ou perderam os papeis ARIA");
    out.push(r);
  }
  return out;
}

async function checkPricing(page, expected) {
  if (!expected) return [];
  const out = [];
  for (const [pid, exp] of Object.entries(expected)) {
    const r = { id: pid, issues: [] };
    const sel = `[data-pricing="${pid}"]`;
    if (!(await page.locator(sel).count())) { r.issues.push("ausente na pagina (data-pricing nao encontrado)"); out.push(r); continue; }
    const read = () => page.evaluate((sel) => {
      const root = document.querySelector(sel);
      const plans = [...root.querySelectorAll("[data-pricing-plan]")];
      return {
        billing: root.dataset.billing,
        toggleVisible: !!root.querySelector("[data-pricing-toggle]:not([hidden])"),
        pressed: [...root.querySelectorAll("[data-billing-option]")].filter((b) => b.getAttribute("aria-pressed") === "true").map((b) => b.dataset.billingOption),
        options: [...root.querySelectorAll("[data-billing-option]")].map((b) => b.dataset.billingOption),
        status: (root.querySelector("[data-pricing-status]")?.textContent || "").trim(),
        plans: plans.map((p) => {
          const shown = [...p.querySelectorAll("[data-price-for]")].filter((d) => !d.hidden);
          return {
            name: (p.querySelector(".pricing__name")?.textContent || "").trim(),
            featured: p.classList.contains("is-featured"),
            badge: (p.querySelector(".pricing__badge")?.textContent || "").trim(),
            shownFor: shown.map((d) => d.dataset.priceFor),
            prices: shown.map((d) => (d.querySelector(".price .screen-reader-text")?.textContent || "").trim()),
            featuresNoText: [...p.querySelectorAll(".pricing__feature")].filter((li) => !li.querySelector(".screen-reader-text")?.textContent.trim()).length,
            cta: p.querySelector(".pricing__cta")?.getAttribute("href") ?? null,
          };
        }),
      };
    }, sel);
    let s = await read();
    if (Number.isInteger(exp.plan_count) && s.plans.length !== exp.plan_count) r.issues.push(`${s.plans.length} plano(s), referencia mostra ${exp.plan_count}`);
    s.plans.forEach((p, i) => {
      const tag = p.name || `plano ${i + 1}`;
      if (!p.name) r.issues.push(`plano ${i + 1} sem nome`);
      if (!p.prices.length) r.issues.push(`${tag}: sem preco visivel`);
      p.prices.filter((t) => !BRL.test(t)).forEach((t) => r.issues.push(`${tag}: preco fora do padrao "R$ 1.234,56" ("${t}")`));
      if (p.featuresNoText) r.issues.push(`${tag}: ${p.featuresNoText} recurso(s) sem "Incluído/Não incluído" para leitor de tela`);
      if (p.cta !== null && (!p.cta || p.cta === "#")) r.issues.push(`${tag}: botao sem destino`);
    });
    if (Number.isInteger(exp.featured_plan)) {
      const f = s.plans[exp.featured_plan - 1];
      if (!f || !f.featured) r.issues.push(`plano ${exp.featured_plan} sem destaque (.is-featured)`);
      else if (!f.badge) r.issues.push(`plano em destaque sem selo em texto`);
    }
    const billing = exp.billing || [];
    if (billing.length > 1) {
      if (!s.toggleVisible) r.issues.push("seletor de periodo nao aparece (pricing.js enfileirado?)");
      else {
        if (s.pressed.join() !== (exp.default_billing || billing[0])) r.issues.push(`periodo selecionado ao carregar: ${s.pressed} (referencia: ${exp.default_billing})`);
        if (s.plans.some((p) => p.shownFor.join() !== s.pressed.join())) r.issues.push("precos visiveis nao batem com o periodo selecionado");
        const other = s.options.find((o) => o !== s.pressed[0]);
        if (other) {
          await page.locator(`${sel} [data-billing-option="${other}"]`).click();
          await page.waitForTimeout(150);
          s = await read();
          if (s.pressed.join() !== other || s.plans.some((p) => p.shownFor.join() !== other)) r.issues.push(`trocar para ${other} nao troca os precos`);
          if (!s.status) r.issues.push("troca de periodo nao e anunciada (aria-live)");
        }
      }
    }
    out.push(r);
  }
  return out;
}

// Depoimentos e logos de clientes (references/social-proof.md).
async function checkTestimonials(page, expected) {
  if (!expected) return [];
  const out = [];
  const selfReviews = await page.evaluate(() => [...document.querySelectorAll('script[type="application/ld+json"]')]
    .some((s) => /"@type"\s*:\s*"(Review|AggregateRating)"/.test(s.textContent)));
  for (const [tid, exp] of Object.entries(expected)) {
    const r = { id: tid, issues: [] };
    const sel = `[data-testimonials="${tid}"]`;
    if (!(await page.locator(sel).count())) { r.issues.push("ausente na pagina (data-testimonials nao encontrado - demo em producao fica oculto)"); out.push(r); continue; }
    const fields = exp.fields_shown || [];
    const info = await page.evaluate((sel) => [...document.querySelectorAll(`${sel} > li`)].map((li) => ({
      quote: (li.querySelector("blockquote")?.textContent || "").trim(),
      name: (li.querySelector(".testimonial__name")?.textContent || "").trim(),
      nameInCite: !!li.querySelector("cite .testimonial__name, cite.testimonial__name"),
      rating: (li.querySelector(".testimonial__rating .screen-reader-text")?.textContent || "").trim(),
      photo: !!li.querySelector(".testimonial__photo"),
    })), sel);
    if (Number.isInteger(exp.item_count) && info.length !== exp.item_count) r.issues.push(`${info.length} depoimento(s), referencia mostra ${exp.item_count}`);
    info.forEach((t, i) => {
      const tag = t.name || `depoimento ${i + 1}`;
      if (!t.quote) r.issues.push(`${tag}: sem texto`);
      if (!t.name) r.issues.push(`depoimento ${i + 1}: sem nome do autor`);
      if (fields.includes("rating") && !/\d(,5)? de 5/.test(t.rating)) r.issues.push(`${tag}: estrelas sem texto "N de 5" para leitor de tela`);
      if (fields.includes("photo") && !t.photo) r.issues.push(`${tag}: sem foto (a referencia mostra)`);
    });
    if (selfReviews) r.issues.push("pagina com JSON-LD Review/AggregateRating (avaliacao autopromocional - remover)");
    out.push(r);
  }
  return out;
}

async function checkClientLogos(page, expected) {
  if (!expected) return [];
  const out = [];
  for (const [cid, exp] of Object.entries(expected)) {
    const r = { id: cid, issues: [] };
    const sel = `[data-client-logos="${cid}"]`;
    if (!(await page.locator(sel).count())) { r.issues.push("ausente na pagina (data-client-logos nao encontrado - demo em producao fica oculto)"); out.push(r); continue; }
    const info = await page.evaluate((sel) => {
      const root = document.querySelector(sel);
      const items = [...root.querySelectorAll(".client-logos__list:not(.client-logos__list--clone) > li")];
      const clone = root.querySelector(".client-logos__list--clone");
      const track = root.querySelector("[data-logos-track]");
      return {
        count: items.length,
        badAlt: items.map((li) => li.querySelector("img")).filter(Boolean).map((img) => img.getAttribute("alt") || "")
          .filter((alt) => !alt.trim() || /\blogo(tipo|marca)?\b/i.test(alt)),
        noName: items.filter((li) => !li.querySelector("img") && !li.textContent.trim()).length,
        js: root.classList.contains("client-logos--js"),
        clone: clone ? { hidden: clone.getAttribute("aria-hidden") === "true", inert: clone.inert } : null,
        toggle: !!root.querySelector("[data-logos-toggle]"),
        animation: track ? getComputedStyle(track).animationName : "none",
        reduce: matchMedia("(prefers-reduced-motion: reduce)").matches,
      };
    }, sel);
    if (Number.isInteger(exp.logo_count) && info.count !== exp.logo_count) r.issues.push(`${info.count} logo(s), referencia mostra ${exp.logo_count}`);
    if (info.badAlt.length) r.issues.push(`${info.badAlt.length} logo(s) com alt vazio ou "logo" (use o nome da empresa): ${info.badAlt.slice(0, 2).map((a) => `"${a}"`).join(", ")}`);
    if (info.noName) r.issues.push(`${info.noName} item(ns) sem logo nem nome`);
    if (exp.layout === "marquee") {
      if (!info.js) r.issues.push("faixa nao inicializou (client-logos.js enfileirado?)");
      else {
        if (!info.clone || !info.clone.hidden || !info.clone.inert) r.issues.push("copia do loop sem aria-hidden/inert (leitor de tela/Tab veem os logos duas vezes)");
        if (!info.toggle) r.issues.push("faixa em movimento sem botao de pausa (WCAG 2.2.2)");
        if (info.reduce && info.animation !== "none") r.issues.push("faixa se move mesmo com prefers-reduced-motion");
      }
    }
    out.push(r);
  }
  return out;
}

// Equipe e numeros em destaque (references/team-stats.md).
async function checkTeam(page, expected) {
  if (!expected) return [];
  const out = [];
  for (const [tid, exp] of Object.entries(expected)) {
    const r = { id: tid, issues: [] };
    const sel = `[data-team="${tid}"]`;
    if (!(await page.locator(sel).count())) { r.issues.push("ausente na pagina (data-team nao encontrado - demo em producao fica oculto)"); out.push(r); continue; }
    const fields = exp.fields_shown || [];
    const people = await page.evaluate((sel) => [...document.querySelectorAll(`${sel} > li`)].map((li) => {
      const name = (li.querySelector(".team-member__name")?.textContent || "").trim();
      const bio = li.querySelector(".team-member__bio");
      const bioStyle = bio ? getComputedStyle(bio) : null;
      return {
        name,
        role: (li.querySelector(".team-member__role")?.textContent || "").trim(),
        photo: !!li.querySelector(".team-member__photo"),
        registration: (li.querySelector(".team-member__registration")?.textContent || "").trim(),
        bio: !!bio,
        bioHoverOnly: !!bio && bio.tagName !== "DETAILS" && (bioStyle.opacity === "0" || bioStyle.visibility === "hidden" || bioStyle.display === "none"),
        socialNoName: [...li.querySelectorAll(".team-member__social a")].filter((a) => !name || !(a.textContent || "").includes(name)).length,
      };
    }), sel);
    if (Number.isInteger(exp.member_count) && people.length !== exp.member_count) r.issues.push(`${people.length} pessoa(s), referencia mostra ${exp.member_count}`);
    people.forEach((p, i) => {
      const tag = p.name || `pessoa ${i + 1}`;
      if (!p.name) r.issues.push(`pessoa ${i + 1}: sem nome`);
      if (fields.includes("role") && !p.role) r.issues.push(`${tag}: sem cargo`);
      if (fields.includes("photo") && !p.photo) r.issues.push(`${tag}: sem foto (a referencia mostra)`);
      if (fields.includes("registration") && !p.registration) r.issues.push(`${tag}: sem registro profissional (exigido pelo setor)`);
      if (fields.includes("bio") && !p.bio) r.issues.push(`${tag}: sem bio`);
      if (p.bioHoverOnly) r.issues.push(`${tag}: bio escondida (so no hover nao funciona no teclado/toque)`);
      if (p.socialNoName) r.issues.push(`${tag}: ${p.socialNoName} rede(s) sem o nome da pessoa no link ("LinkedIn de ...")`);
    });
    out.push(r);
  }
  return out;
}

async function checkStats(page, expected) {
  if (!expected) return [];
  const out = [];
  for (const [sid, exp] of Object.entries(expected)) {
    const r = { id: sid, issues: [] };
    const sel = `[data-stats="${sid}"]`;
    if (!(await page.locator(sel).count())) { r.issues.push("ausente na pagina (data-stats nao encontrado - demo em producao fica oculto)"); out.push(r); continue; }
    const info = await page.evaluate((sel) => ({
      reduce: matchMedia("(prefers-reduced-motion: reduce)").matches,
      countUp: document.querySelector(sel).dataset.countUp === "true",
      items: [...document.querySelectorAll(`${sel} > li`)].map((li) => ({
        final: (li.querySelector(".stat__value .screen-reader-text")?.textContent || "").trim(),
        visual: (li.querySelector(".stat__number")?.textContent || "").trim(),
        animated: li.querySelector(".stat__number")?.dataset.animated || null,
        label: (li.querySelector(".stat__label")?.textContent || "").trim(),
      })),
    }), sel);
    if (Number.isInteger(exp.item_count) && info.items.length !== exp.item_count) r.issues.push(`${info.items.length} numero(s), referencia mostra ${exp.item_count}`);
    if (typeof exp.count_up === "boolean" && exp.count_up !== info.countUp) r.issues.push(`contagem animada ${info.countUp}, Blueprint diz ${exp.count_up}`);
    info.items.forEach((s, i) => {
      const tag = s.label || `numero ${i + 1}`;
      if (!/\d/.test(s.final)) r.issues.push(`${tag}: valor final ausente no HTML (leitor de tela/buscador/sem JS)`);
      if (!s.label) r.issues.push(`numero ${i + 1}: sem rotulo`);
      if (info.reduce && (s.animated || s.visual !== s.final)) r.issues.push(`${tag}: anima com prefers-reduced-motion ou mostra "${s.visual}" em vez de "${s.final}"`);
    });
    out.push(r);
  }
  return out;
}

// Blog (references/blog.md): roda em toda pagina e reage ao que encontra -
// secao de ultimos posts, indice/arquivo do blog, post individual.
async function checkBlog(page, exp) {
  if (!exp) return null;
  const info = await page.evaluate(() => {
    const iso = (s) => !!s && /^\d{4}-\d{2}-\d{2}T/.test(s) && !isNaN(Date.parse(s));
    const cards = [...document.querySelectorAll("[data-post-card]")].map((c) => ({
      title: (c.querySelector(".post-card__title")?.textContent || "").trim(),
      links: c.querySelectorAll("a.post-card__link").length,
      otherLinks: [...c.querySelectorAll("a")].filter((a) => !a.classList.contains("post-card__link") && !a.classList.contains("post-category")).length,
      time: c.querySelector("time") ? iso(c.querySelector("time").getAttribute("datetime")) : null,
      category: !!c.querySelector(".post-category"),
      image: !!c.querySelector(".post-card__image"),
    }));
    const latest = document.querySelector("[data-posts-latest]");
    const index = document.querySelector("[data-posts-index]");
    const single = document.querySelector("[data-post-single]");
    const pag = document.querySelector("nav.pagination");
    let ld = null;
    for (const s of document.querySelectorAll('script[type="application/ld+json"]')) {
      try { const d = JSON.parse(s.textContent); if (d["@type"] === "BlogPosting" || d["@type"] === "Article") ld = d; } catch {}
    }
    return {
      cards,
      latestCount: latest ? latest.querySelectorAll("[data-post-card]").length : null,
      indexCount: index ? index.querySelectorAll("[data-post-card]").length : null,
      pagination: pag ? { label: pag.getAttribute("aria-label"), current: pag.querySelectorAll('[aria-current="page"]').length } : null,
      single: single ? {
        h1: (single.querySelector("h1")?.textContent || "").trim(),
        time: single.querySelector(".post-single__meta time") ? iso(single.querySelector(".post-single__meta time").getAttribute("datetime")) : false,
        image: single.querySelector(".post-single__image img")?.getAttribute("fetchpriority") || (single.querySelector(".post-single__image") ? "none" : null),
        shareNoName: [...single.querySelectorAll(".post-share a")].filter((a) => !a.textContent.trim()).length,
        ld: ld ? { headline: ld.headline, published: iso(ld.datePublished), author: !!ld.author?.name } : null,
      } : null,
      trackers: [...document.scripts].map((s) => s.src).filter((src) => /addthis|sharethis|connect\.facebook\.net|platform\.twitter|widgets\.js/.test(src)),
    };
  });
  const issues = [];
  const fields = exp.card_fields || [];
  info.cards.forEach((c, i) => {
    const tag = c.title || `card ${i + 1}`;
    if (!c.title) issues.push(`card ${i + 1}: sem titulo`);
    if (c.links !== 1) issues.push(`${tag}: ${c.links} link(s) de titulo (deve ser 1, esticado sobre o card)`);
    if (c.otherLinks) issues.push(`${tag}: ${c.otherLinks} link(s) extra(s) no card (imagem/"Leia mais" duplicam o link)`);
    if (fields.includes("date") && c.time !== true) issues.push(`${tag}: data sem <time datetime> ISO`);
    if (fields.includes("category") && !c.category) issues.push(`${tag}: sem categoria`);
    if (fields.includes("image") && !c.image) issues.push(`${tag}: sem moldura de imagem`);
  });
  if (info.latestCount !== null && Number.isInteger(exp.home_count) && info.latestCount !== exp.home_count) issues.push(`secao de ultimos posts com ${info.latestCount} post(s), referencia mostra ${exp.home_count}`);
  if (info.indexCount !== null && Number.isInteger(exp.posts_per_page) && info.indexCount > exp.posts_per_page) issues.push(`listagem com ${info.indexCount} posts (posts_per_page ${exp.posts_per_page})`);
  if (info.pagination) {
    if (!info.pagination.label) issues.push("paginacao sem aria-label");
    if (info.pagination.current !== 1) issues.push("paginacao sem a pagina atual marcada (aria-current)");
  }
  if (info.single) {
    if (!info.single.h1) issues.push("post sem <h1>");
    if (!info.single.time) issues.push("post sem data em <time datetime> ISO");
    if (info.single.image && info.single.image !== "high") issues.push("imagem de destaque sem fetchpriority=high (e o LCP)");
    if (info.single.shareNoName) issues.push(`${info.single.shareNoName} link(s) de compartilhar sem nome acessivel`);
    if (!info.single.ld) issues.push("post sem JSON-LD BlogPosting/Article");
    else {
      if (info.single.ld.headline !== info.single.h1) issues.push(`JSON-LD headline "${info.single.ld.headline}" difere do titulo`);
      if (!info.single.ld.published || !info.single.ld.author) issues.push("JSON-LD sem datePublished ISO ou author");
    }
  }
  if (info.trackers.length) issues.push(`script de compartilhamento de terceiros: ${info.trackers[0]}`);
  return { id: "blog", issues, cards: info.cards.length, single: !!info.single, index: info.indexCount !== null };
}

// Rodape e redes (references/footer-social.md): roda em toda pagina.
async function checkFooter(page, exp, isHome) {
  if (!exp) return null;
  const info = await page.evaluate(() => {
    const footer = document.querySelector("[data-site-footer]") || document.querySelector("footer");
    if (!footer) return null;
    // Validade de TODOS os links de rede da pagina (header, rodape, contato);
    // a contagem e so do rodape (redes no header + rodape sao legitimas).
    const footerSocial = footer.querySelectorAll(".social-links a").length;
    const social = [...document.querySelectorAll(".social-links a")].map((a) => ({
      href: a.getAttribute("href") || "",
      name: (a.textContent || a.getAttribute("aria-label") || "").replace(/\s+/g, " ").trim(),
      icon: !!a.querySelector("svg, img"),
    }));
    let org = null;
    for (const s of document.querySelectorAll('script[type="application/ld+json"]')) {
      try { const d = JSON.parse(s.textContent); if (d["@type"] === "Organization") org = d; } catch {}
    }
    return {
      columns: [...footer.querySelectorAll("[data-footer-col]")].map((c) => ({
        id: c.dataset.footerCol, title: (c.querySelector(".footer-col__title")?.textContent || "").trim(),
      })),
      social,
      footerSocial,
      deadLinks: [...footer.querySelectorAll("a")].filter((a) => { const h = (a.getAttribute("href") || "").trim(); return !h || h === "#"; }).length,
      tel: [...footer.querySelectorAll('a[href^="tel:"]')].map((a) => a.getAttribute("href")),
      wa: [...footer.querySelectorAll('a[href*="wa.me"], a[href*="api.whatsapp.com"]')].map((a) => a.getAttribute("href")),
      mail: [...footer.querySelectorAll('a[href^="mailto:"]')].map((a) => a.getAttribute("href")),
      privacy: [...footer.querySelectorAll("a")].some((a) => /privacidade|privacy/i.test(a.textContent + " " + a.getAttribute("href"))),
      text: footer.textContent.replace(/\s+/g, " "),
      org: org ? { sameAs: org.sameAs || [] } : null,
    };
  });
  const issues = [];
  if (!info) return { id: "footer", issues: ["rodape ausente"] };
  const cols = exp.columns || [];
  if (cols.length) {
    const got = info.columns.map((c) => c.id).join(",");
    const want = cols.map((c) => c.id).join(",");
    if (got !== want) issues.push(`colunas [${got}] (referencia: [${want}])`);
    cols.filter((c) => c.title).forEach((c) => {
      const col = info.columns.find((x) => x.id === c.id);
      if (col && col.title !== c.title) issues.push(`coluna ${c.id}: titulo "${col.title}" (referencia: "${c.title}")`);
    });
  }
  if (info.deadLinks) issues.push(`${info.deadLinks} link(s) sem destino no rodape (href vazio ou #)`);
  const networks = exp.networks || [];
  info.social.forEach((s, i) => {
    if (!/^https?:\/\//.test(s.href)) issues.push(`rede ${i + 1}: link invalido "${s.href}"`);
    if (!s.name) issues.push(`rede ${i + 1}: sem nome acessivel`);
    if (!s.icon) issues.push(`rede ${i + 1}: sem icone`);
  });
  if (networks.length && info.footerSocial > networks.length) issues.push(`${info.footerSocial} icone(s) de rede no rodape, referencia mostra ${networks.length}`);
  info.tel.filter((h) => !/^tel:\+\d{12,15}$/.test(h)).forEach((h) => issues.push(`telefone com link invalido "${h}" (use tel:+55...)`));
  info.wa.filter((h) => !/^https:\/\/wa\.me\/\d{12,15}(\?text=.*)?$/.test(h)).forEach((h) => issues.push(`WhatsApp com link invalido "${h}" (use https://wa.me/55...)`));
  info.mail.filter((h) => !/^mailto:[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(h)).forEach((h) => issues.push(`e-mail com link invalido "${h}"`));
  if (exp.privacy_link && !info.privacy) issues.push("sem link da politica de privacidade (LGPD)");
  if (exp.dynamic_year && !info.text.includes(String(new Date().getFullYear()))) issues.push(`copyright sem o ano atual (${new Date().getFullYear()})`);
  if (isHome && info.social.length) {
    const profiles = [...new Set(info.social.map((s) => s.href).filter((h) => !/wa\.me|whatsapp/.test(h)))].sort();
    if (!info.org) issues.push("Home sem JSON-LD Organization (sameAs liga o site aos perfis)");
    else if (JSON.stringify([...info.org.sameAs].sort()) !== JSON.stringify(profiles)) issues.push("JSON-LD Organization.sameAs difere dos perfis do rodape");
  }
  return { id: "footer", issues };
}

// Header e menu (references/header-menu.md): roda em toda pagina.
async function checkHeader(page, exp, viewport, isHome) {
  if (!exp) return null;
  const issues = [];
  const base = await page.evaluate((home) => {
    const h = document.querySelector("[data-site-header]");
    if (!h) return null;
    const logo = h.querySelector("a.site-logo");
    const img = logo?.querySelector("img");
    const nav = h.querySelector("[data-nav]");
    const top = nav ? [...nav.querySelectorAll(":scope > ul > li > a, :scope > div > ul > li > a")].map((a) => a.textContent.replace(/\s+/g, " ").trim()) : [];
    const cta = h.querySelector(".site-header__cta");
    const tb = document.querySelector("[data-site-topbar]");
    return {
      logo: logo ? { home: logo.href.replace(/\/$/, "") === home.replace(/\/$/, ""),
        named: !!((img && img.getAttribute("alt")) || logo.textContent.trim()), sized: !img || (img.hasAttribute("width") && img.hasAttribute("height")) } : null,
      top,
      cta: cta ? { text: cta.textContent.trim(), href: cta.getAttribute("href") || "" } : null,
      topbar: tb ? { tel: [...tb.querySelectorAll('a[href^="tel:"]')].map((a) => a.getAttribute("href")), mail: [...tb.querySelectorAll('a[href^="mailto:"]')].map((a) => a.getAttribute("href")) } : null,
      search: h.querySelector("[data-header-search] summary") ? !!h.querySelector("[data-header-search] summary").textContent.trim() : null,
      // Nome acessivel = texto SEM o conteudo aria-hidden (icone/emoji) ou aria-label.
      unnamedActions: [...h.querySelectorAll(".site-header__action")].filter((a) => {
        const c = a.cloneNode(true);
        c.querySelectorAll('[aria-hidden="true"]').forEach((x) => x.remove());
        return !c.textContent.trim() && !a.getAttribute("aria-label");
      }).length,
      parents: [...h.querySelectorAll("[data-nav] .menu-item-has-children")].length,
      toggles: [...h.querySelectorAll(".submenu-toggle")].map((b) => ({ expanded: b.getAttribute("aria-expanded"), controls: b.getAttribute("aria-controls"), name: b.textContent.trim() })),
    };
  }, config.base);
  if (!base) return { id: "header", issues: ["header ausente"] };
  if (!base.logo) issues.push("sem logo com link para a Home (a.site-logo)");
  else {
    if (!base.logo.home) issues.push("logo nao leva para a Home");
    if (!base.logo.named) issues.push("logo sem nome acessivel (alt = nome da empresa)");
    if (!base.logo.sized) issues.push("logo sem width/height (salto de layout)");
  }
  const labels = exp.menu_labels || [];
  if (labels.length && viewport === "desktop" && base.top.join("|") !== labels.join("|")) issues.push(`menu [${base.top.join(", ")}] (referencia: [${labels.join(", ")}])`);
  if (exp.cta) {
    if (!base.cta) issues.push(`sem botao de destaque "${exp.cta}"`);
    else {
      if (base.cta.text !== exp.cta) issues.push(`botao "${base.cta.text}" (referencia: "${exp.cta}")`);
      if (!base.cta.href || base.cta.href === "#") issues.push("botao de destaque sem destino");
    }
  }
  if ((exp.top_bar || []).length) {
    if (!base.topbar) issues.push("sem barra superior");
    else {
      base.topbar.tel.filter((h) => !/^tel:\+\d{12,15}$/.test(h)).forEach((h) => issues.push(`barra superior: telefone invalido "${h}"`));
      base.topbar.mail.filter((h) => !/^mailto:[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(h)).forEach((h) => issues.push(`barra superior: e-mail invalido "${h}"`));
    }
  }
  if ((exp.actions || []).includes("search") && !base.search) issues.push("busca do header ausente ou sem nome acessivel");
  if (base.unnamedActions) issues.push(`${base.unnamedActions} icone(s) de acao sem nome acessivel`);

  // Submenus: botao por item com filhos; teclado abre, Esc fecha e devolve o foco.
  if (base.parents) {
    if (base.toggles.length !== base.parents) issues.push(`${base.parents} item(ns) com submenu, ${base.toggles.length} botao(oes) - submenu so no hover nao funciona no teclado/toque`);
    else if (base.toggles.some((t) => !t.name || !t.controls || t.expanded !== "false")) issues.push("botao de submenu sem nome, aria-controls ou aria-expanded");
    else {
      const mobile = viewport === "mobile";
      if (mobile) await page.locator("[data-nav-toggle]").click().catch(() => {});
      const btn = page.locator("[data-site-header] .submenu-toggle").first();
      await btn.focus();
      await page.keyboard.press("Enter");
      await page.waitForTimeout(100);
      const opened = await page.evaluate(() => {
        const b = document.querySelector("[data-site-header] .submenu-toggle");
        const sub = document.getElementById(b.getAttribute("aria-controls"));
        return { expanded: b.getAttribute("aria-expanded"), visible: !!sub && sub.offsetParent !== null };
      });
      if (opened.expanded !== "true" || !opened.visible) issues.push("Enter no botao nao abre o submenu");
      await page.keyboard.press("Escape");
      await page.waitForTimeout(100);
      const closed = await page.evaluate(() => {
        const b = document.querySelector("[data-site-header] .submenu-toggle");
        return { expanded: b.getAttribute("aria-expanded"), focusBack: document.activeElement === b };
      });
      if (closed.expanded !== "false" || !closed.focusBack) issues.push("Esc nao fecha o submenu ou nao devolve o foco ao botao");
      if (!mobile) {
        await btn.focus();
        await page.keyboard.press("ArrowDown");
        await page.waitForTimeout(100);
        const inSub = await page.evaluate(() => !!document.activeElement.closest(".sub-menu"));
        if (!inSub) issues.push("seta para baixo no botao nao leva ao primeiro item do submenu");
        await page.keyboard.press("Escape");
      }
      if (mobile) await page.keyboard.press("Escape");
    }
  }

  // Menu mobile: abre o painel, Esc fecha e devolve o foco.
  if (viewport === "mobile") {
    const t = page.locator("[data-nav-toggle]");
    if (await t.isVisible().catch(() => false)) {
      await t.click();
      await page.waitForTimeout(100);
      const open = await page.evaluate(() => ({ exp: document.querySelector("[data-nav-toggle]").getAttribute("aria-expanded"), vis: document.querySelector("[data-nav-panel]")?.offsetParent !== null }));
      if (open.exp !== "true" || !open.vis) issues.push("botao do menu mobile nao abre o painel");
      await page.keyboard.press("Escape");
      await page.waitForTimeout(100);
      const shut = await page.evaluate(() => ({ exp: document.querySelector("[data-nav-toggle]").getAttribute("aria-expanded"), focus: document.activeElement === document.querySelector("[data-nav-toggle]") }));
      if (shut.exp !== "false" || !shut.focus) issues.push("Esc nao fecha o menu mobile ou nao devolve o foco");
    } else issues.push("menu mobile sem botao visivel");
  }

  // Header transparente na Home: sem fundo no topo; com fundo ao rolar (sticky).
  if (exp.transparent && isHome && viewport === "desktop") {
    const alpha = () => page.evaluate(() => {
      const m = getComputedStyle(document.querySelector("[data-site-header]")).backgroundColor.match(/[\d.]+/g) || [];
      return m.length === 4 ? parseFloat(m[3]) : (getComputedStyle(document.querySelector("[data-site-header]")).backgroundColor === "transparent" ? 0 : 1);
    });
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(200);
    if ((await alpha()) !== 0) issues.push("header transparente com fundo no topo (sobre o hero)");
    // Sobre a foto, o texto do menu tem de usar a cor definida para o header
    // transparente (nao o azul padrao de link): proxy de contraste.
    const off = await page.evaluate(() => {
      const h = document.querySelector("[data-site-header]");
      const c = getComputedStyle(h).color;
      return [...h.querySelectorAll("[data-nav] > ul > li > a")].filter((a) => getComputedStyle(a).color !== c).map((a) => a.textContent.trim());
    });
    if (off.length) issues.push(`no header transparente, ${off.length} link(s) do menu com cor diferente da do header (contraste sobre o hero): ${off.slice(0, 3).join(", ")}`);
    if (exp.sticky) {
      await page.evaluate(() => window.scrollTo(0, 600));
      await page.waitForTimeout(400);
      if ((await alpha()) < 1) issues.push("header transparente sem fundo ao rolar (texto sobre o conteudo)");
      await page.evaluate(() => window.scrollTo(0, 0));
    }
  }
  return { id: "header", issues };
}

// Estabilidade do layout: soma dos layout-shift sem input recente (CLS).
const CLS_OBSERVER = `(() => {
  window.__qaCls = 0; window.__qaShifts = [];
  const name = (n) => !n || !n.nodeName ? "?" : n.nodeName.toLowerCase() + (n.id ? "#" + n.id : "")
    + (typeof n.className === "string" && n.className.trim() ? "." + n.className.trim().split(/\\s+/)[0] : "");
  try {
    new PerformanceObserver((list) => {
      for (const e of list.getEntries()) {
        if (e.hadRecentInput) continue;
        window.__qaCls += e.value;
        window.__qaShifts.push({ v: e.value, src: (e.sources || []).slice(0, 3).map((s) => name(s.node)) });
        window.__qaShifts.sort((a, b) => b.v - a.v);
      }
    }).observe({ type: "layout-shift", buffered: true });
  } catch (e) {}
  window.__qaLcp = null;
  try {
    new PerformanceObserver((list) => {
      const e = list.getEntries().at(-1);
      if (e) window.__qaLcp = { t: e.startTime, el: name(e.element) };
    }).observe({ type: "largest-contentful-paint", buffered: true });
  } catch (e) {}
})();`;

// Desempenho (references/performance.md): tempos e peso medidos no carregamento
// LOCAL - servem para achar excessos e comparar antes/depois, nao como numero
// de producao. Limites "bom / precisa melhorar / ruim" do Core Web Vitals.
async function measurePerformance(page) {
  const m = await page.evaluate(() => {
    const nav = performance.getEntriesByType("navigation")[0] || {};
    const fcp = performance.getEntriesByName("first-contentful-paint")[0];
    const types = { js: 0, css: 0, img: 0, font: 0, other: 0 };
    let total = nav.encodedBodySize || nav.transferSize || 0;
    const res = performance.getEntriesByType("resource");
    for (const r of res) {
      const size = r.encodedBodySize || r.transferSize || 0;
      total += size;
      const url = r.name.split("?")[0].toLowerCase();
      const k = /\.(js|mjs)$/.test(url) || r.initiatorType === "script" ? "js"
        : /\.css$/.test(url) || (r.initiatorType === "link" && !/\.(woff2?|ttf|otf)$/.test(url)) ? "css"
        : /\.(woff2?|ttf|otf)$/.test(url) ? "font"
        : /\.(jpe?g|png|webp|avif|gif|svg)$/.test(url) || r.initiatorType === "img" ? "img" : "other";
      types[k] += size;
    }
    return { ttfb: Math.round(nav.responseStart || 0), fcp: fcp ? Math.round(fcp.startTime) : null,
             lcp: window.__qaLcp ? Math.round(window.__qaLcp.t) : null, lcpEl: window.__qaLcp ? window.__qaLcp.el : null,
             kb: Math.round(total / 1024), requests: res.length + 1, dom: document.getElementsByTagName("*").length,
             byType: Object.fromEntries(Object.entries(types).map(([k, v]) => [k, Math.round(v / 1024)])) };
  });
  const issues = [];
  const notes = [];
  const grade = (v, good, poor, label, unit = "ms") => {
    if (v == null) return;
    if (v > poor) issues.push(`${label} ${v}${unit} (ruim: acima de ${poor}${unit})`);
    else if (v > good) notes.push(`${label} ${v}${unit} (precisa melhorar: acima de ${good}${unit})`);
  };
  grade(m.ttfb, 800, 1800, "resposta do servidor (TTFB)");
  grade(m.lcp, 2500, 4000, `maior elemento (LCP: ${m.lcpEl || "?"})`);
  grade(m.fcp, 1800, 3000, "primeira pintura (FCP)");
  if (m.kb > 3072) issues.push(`pagina com ${(m.kb / 1024).toFixed(1)} MB (acima de 3 MB)`);
  if (m.requests > 80) notes.push(`${m.requests} arquivos baixados (acima de 80)`);
  if (m.dom > 1500) notes.push(`${m.dom} elementos no HTML (acima de 1.500 deixa o celular lento)`);
  if (m.byType.js > 500) notes.push(`${m.byType.js} KB de JavaScript (acima de 500 KB)`);
  if (m.byType.css > 200) notes.push(`${m.byType.css} KB de CSS (acima de 200 KB)`);
  return { id: "desempenho", ...m, issues, notes };
}

// Imagens: peso, tamanho maior que o exibido, sem dimensoes (pulo) e
// fora da tela sem lazy. Rodar DEPOIS da rolagem (imagens lazy carregadas).
async function checkImages(page) {
  const list = await page.evaluate(() => {
    const vh = innerHeight;
    return [...document.images].filter((img) => img.complete && img.naturalWidth && img.getBoundingClientRect().width > 1).map((img) => {
      const r = img.getBoundingClientRect();
      const res = performance.getEntriesByName(img.currentSrc)[0];
      const cs = getComputedStyle(img);
      return {
        src: (img.currentSrc || img.src).split("/").pop().split("?")[0].slice(0, 60),
        natural: img.naturalWidth, shown: Math.round(r.width),
        kb: res ? Math.round((res.encodedBodySize || res.transferSize || 0) / 1024) : null,
        dims: img.hasAttribute("width") && img.hasAttribute("height"),
        sized: cs.aspectRatio !== "auto" || !!img.closest(".media-frame") || cs.position === "absolute",
        top: Math.round(r.top + scrollY), lazy: img.loading === "lazy", hero: !!img.closest("[data-hero]"), vh,
      };
    });
  });
  const issues = [];
  const notes = [];
  for (const i of list) {
    if (i.kb != null && i.kb > 400) issues.push(`${i.src}: ${i.kb} KB (foto pesada - use ate ~200 KB; o WordPress gera tamanhos menores se a imagem vier da Midia)`);
    else if (i.kb != null && i.kb > 200) notes.push(`${i.src}: ${i.kb} KB`);
    if (i.natural > i.shown * 2.5 && (i.kb == null || i.kb > 100)) notes.push(`${i.src}: ${i.natural}px exibida a ${i.shown}px (srcset/tamanho menor)`);
    if (!i.dims && !i.sized) notes.push(`${i.src}: sem width/height nem proporcao - a pagina pula quando ela carrega`);
    if (!i.hero && !i.lazy && i.top > i.vh * 1.5) notes.push(`${i.src}: fora da tela sem loading="lazy"`);
  }
  return { id: "imagens", count: list.length, kb: list.reduce((s, i) => s + (i.kb || 0), 0), issues: [...new Set(issues)], notes: [...new Set(notes)].slice(0, 12) };
}

// Fontes (references/fonts.md): de onde vem, se carregou o peso usado,
// font-display, preload usado e com crossorigin, reserva ajustada.
async function checkFonts(page, exp) {
  const info = await page.evaluate(async () => {
    await document.fonts.ready;
    const rules = [];
    for (const sheet of document.styleSheets) {
      let list;
      try { list = sheet.cssRules; } catch { continue; }   // folha de outro dominio
      for (const r of list || []) {
        if (r.constructor.name !== "CSSFontFaceRule") continue;
        const src = r.style.getPropertyValue("src");
        rules.push({
          family: r.style.getPropertyValue("font-family").replace(/["']/g, "").trim(),
          weight: r.style.getPropertyValue("font-weight") || "400",
          display: r.style.getPropertyValue("font-display") || "auto",
          sizeAdjust: r.style.getPropertyValue("size-adjust") || "",
          urls: [...src.matchAll(/url\(["']?([^"')]+)["']?\)/g)].map((m) => new URL(m[1], sheet.href || location.href).href),
          local: /local\(/.test(src),
        });
      }
    }
    const faces = [...document.fonts].map((f) => ({ family: f.family.replace(/["']/g, ""), weight: String(f.weight), style: f.style, status: f.status }));
    const resources = performance.getEntriesByType("resource")
      .filter((r) => /\.(woff2?|ttf|otf|eot)(\?|$)/i.test(r.name) || /fonts\.(googleapis|gstatic)\.com/.test(r.name))
      .map((r) => ({ url: r.name, bytes: r.encodedBodySize || r.transferSize || 0 }));
    const preloads = [...document.querySelectorAll('link[rel~="preload"][as="font"]')].map((l) => ({ href: l.href, crossorigin: l.hasAttribute("crossorigin") }));
    const used = new Map();
    for (const el of document.querySelectorAll("h1,h2,h3,h4,p,a,li,button,label,blockquote")) {
      if (!el.getClientRects().length || !el.textContent.trim()) continue;
      const cs = getComputedStyle(el);
      const stack = cs.fontFamily.split(",").map((s) => s.replace(/["']/g, "").trim());
      const key = `${stack[0]}|${cs.fontWeight}|${cs.fontStyle}`;
      if (!used.has(key)) used.set(key, { family: stack[0], weight: Number(cs.fontWeight), style: cs.fontStyle, stack, sample: el.tagName.toLowerCase() });
    }
    return { rules, faces, resources, preloads, used: [...used.values()], origin: location.origin };
  });
  const issues = [];
  const notes = [];
  const delivery = exp ? exp.delivery : null;
  const third = info.resources.filter((r) => !r.url.startsWith(info.origin));
  if (third.length && delivery !== "google_cdn") {
    issues.push(`${third.length} fonte(s) de outro dominio (${new URL(third[0].url).host}) - o navegador do visitante envia o IP a terceiro (LGPD); hospede no site (fetch_fonts.py)`);
  }
  const families = new Map(((exp && exp.families) || []).map((f) => [f.family.toLowerCase(), f]));
  const inRange = (w, spec) => { const [a, b] = String(spec).split(/\s+/).map(Number); return b ? w >= a && w <= b : w === a; };
  for (const u of info.used) {
    if (!families.has(u.family.toLowerCase())) continue;
    const loaded = info.faces.filter((f) => f.family.toLowerCase() === u.family.toLowerCase() && f.status === "loaded" && f.style === (u.style === "italic" ? "italic" : "normal"));
    if (!loaded.length) issues.push(`${u.family} ${u.weight} (${u.sample}) nao carregou - o texto aparece na reserva`);
    else if (!loaded.some((f) => inRange(u.weight, f.weight))) {
      const heavier = loaded.some((f) => Number(String(f.weight).split(/\s+/).pop()) >= 600);
      (u.weight >= 600 && !heavier ? issues : notes).push(`${u.family} peso ${u.weight} (${u.sample}) sem arquivo proprio${u.weight >= 600 && !heavier ? " - negrito sintetico (borrado)" : ""}; declare o peso em fonts.families`);
    }
    if (exp && exp.fallback_metrics && !u.stack.some((s) => /fallback$/i.test(s))) {
      issues.push(`font-family de ${u.sample} sem '${u.family} Fallback' - regere tokens.css (generate_design_tokens.py)`);
    }
  }
  for (const r of info.rules.filter((r) => !r.local)) {
    if (!["swap", "fallback", "optional"].includes(r.display)) issues.push(`@font-face ${r.family} ${r.weight} com font-display ${r.display} - texto invisivel ate a fonte chegar`);
  }
  if (exp && exp.fallback_metrics && exp.delivery === "self_hosted") {
    for (const fam of families.values()) {
      if (!info.rules.some((r) => r.family.toLowerCase() === `${fam.family.toLowerCase()} fallback` && r.sizeAdjust)) {
        issues.push(`sem @font-face '${fam.family} Fallback' com size-adjust - o texto pula quando a fonte chega`);
      }
    }
  }
  const urls = info.resources.map((r) => r.url);
  for (const p of info.preloads) {
    if (!p.crossorigin) issues.push(`preload sem crossorigin: ${p.href.split("/").pop()} e baixado duas vezes`);
    const rule = info.rules.find((r) => r.urls.includes(p.href));
    if (!rule) issues.push(`preload de ${p.href.split("/").pop()} que nenhuma @font-face usa (download desperdicado)`);
    else if (!info.used.some((u) => u.family.toLowerCase() === rule.family.toLowerCase() && inRange(u.weight, rule.weight))) {
      notes.push(`preload de ${p.href.split("/").pop()} sem texto que o use nesta pagina`);
    }
  }
  if (info.preloads.length > 2) notes.push(`${info.preloads.length} fontes pre-carregadas (recomendado ate 2)`);
  const dup = urls.filter((u, i) => urls.indexOf(u) !== i);
  if (dup.length) issues.push(`fonte baixada duas vezes: ${[...new Set(dup)].map((u) => u.split("/").pop()).join(", ")}`);
  const kb = Math.round(info.resources.reduce((s, r) => s + r.bytes, 0) / 1024);
  if (kb > 250) notes.push(`${kb} KB de fontes nesta pagina (recomendado ate ~250 KB)`);
  return { id: "fontes", issues: [...new Set(issues)], notes: [...new Set(notes)], files: info.resources.length, kb, preloads: info.preloads.length,
           used: info.used.map((u) => `${u.family} ${u.weight}${u.style === "italic" ? " italico" : ""}`) };
}

async function measureFontSwap(browser, url, vp) {
  const measure = async (blockFonts) => {
    const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: 1, reducedMotion: "reduce" });
    const page = await ctx.newPage();
    if (blockFonts) await page.route(/\.(woff2?|ttf|otf)(\?.*)?$|fonts\.gstatic\.com/i, (r) => r.abort());
    await page.goto(url, { waitUntil: "networkidle", timeout: 45000 });
    const data = await page.evaluate(async () => {
      await document.fonts.ready;
      const pick = (sel) => [...document.querySelectorAll(sel)].find((el) => el.getClientRects().length && el.textContent.trim());
      const out = {};
      for (const [key, sel] of [["h1", "h1"], ["texto", "main p, .hero p, p"], ["menu", "nav a"], ["botao", ".button, button"]]) {
        const el = pick(sel);
        if (!el) continue;
        const r = el.getBoundingClientRect();
        const lh = parseFloat(getComputedStyle(el).lineHeight) || parseFloat(getComputedStyle(el).fontSize) * 1.2;
        out[key] = { top: r.top + scrollY, height: r.height, width: r.width, lines: Math.round(r.height / lh) };
      }
      return { els: out, doc: document.documentElement.scrollHeight };
    });
    await ctx.close();
    return data;
  };
  const fallback = await measure(true);
  const web = await measure(false);
  const items = Object.keys(web.els).filter((k) => fallback.els[k]).map((k) => {
    const a = fallback.els[k], b = web.els[k];
    return { el: k, linesFallback: a.lines, linesWeb: b.lines, heightDelta: Math.round(b.height - a.height),
             widthDeltaPct: a.width ? Math.round(((b.width - a.width) / a.width) * 100) : 0, bottomDelta: Math.round((b.top + b.height) - (a.top + a.height)) };
  });
  const worst = items.reduce((m, i) => Math.max(m, Math.abs(i.bottomDelta)), 0);
  const notes = items.filter((i) => i.linesFallback !== i.linesWeb).map((i) => `${i.el}: ${i.linesFallback} -> ${i.linesWeb} linha(s) na troca`);
  if (worst > 16) notes.push(`texto se move ate ${worst}px quando a fonte chega`);
  return { items, docDelta: web.doc - fallback.doc, worstShift: worst, notes };
}

// SEO da pagina (references/security-seo.md): titulo, descricao, canonico,
// Open Graph, robots e JSON-LD - o que o Google e as redes leem. Titulos e
// descricoes repetidos entre paginas: capture_site.py (visao do site todo).
async function checkSeo(page, exp, ctx) {
  const info = await page.evaluate(() => {
    const content = (sel) => [...document.querySelectorAll(sel)].map((m) => (m.getAttribute("content") || "").trim());
    const og = {};
    for (const p of ["og:title", "og:description", "og:url", "og:image", "og:type", "og:locale", "og:site_name"]) og[p] = content(`meta[property="${p}"]`);
    return {
      title: document.title.trim(),
      descriptions: content('meta[name="description"]'),
      canonicals: [...document.querySelectorAll('link[rel="canonical"]')].map((l) => l.href),
      robots: content('meta[name="robots"]').join(","),
      og,
      twitter: content('meta[name="twitter:card"]'),
      generator: content('meta[name="generator"]').filter((c) => /wordpress/i.test(c)),
      ld: [...document.querySelectorAll('script[type="application/ld+json"]')].map((s) => s.textContent),
      location: location.href.split("#")[0].split("?")[0],
      icons: document.querySelectorAll('link[rel~="icon"]').length,
      apple: !!document.querySelector('link[rel="apple-touch-icon"]'),
      manifest: document.querySelector('link[rel="manifest"]')?.href || null,
      themeColor: document.querySelector('meta[name="theme-color"]')?.content || null,
      feed: !!document.querySelector('link[rel="alternate"][type="application/rss+xml"]'),
    };
  });
  const issues = [];
  const notes = [];
  const noindex = /noindex/i.test(info.robots);
  const wantNoindex = !!(exp && exp.noindex);
  if (wantNoindex && !noindex) issues.push("Blueprint marca 'esconder dos buscadores' e a pagina nao tem noindex");
  if (!wantNoindex && noindex) issues.push("pagina com noindex (some do Google) e o Blueprint nao pede");
  if (!info.title) issues.push("sem <title>");
  else if (info.title.length > 65) notes.push(`titulo com ${info.title.length} caracteres (o Google corta perto de 60)`);
  if (info.descriptions.length > 1) issues.push(`${info.descriptions.length} meta description (tema e plugin de SEO ao mesmo tempo?)`);
  const desc = info.descriptions[0] || "";
  if (!noindex) {
    if (!desc) issues.push("sem meta description (o Google inventa um trecho da pagina)");
    else if (desc.length < 50 || desc.length > 160) notes.push(`descricao com ${desc.length} caracteres (ideal 120-160)`);
    if (exp && exp.description && desc && desc.replace(/\s+/g, " ") !== String(exp.description).trim().replace(/\s+/g, " ")) {
      issues.push(`descricao diferente da aprovada no Blueprint: "${desc.slice(0, 80)}"`);
    }
    if (info.canonicals.length !== 1) issues.push(`${info.canonicals.length} link canonical (esperado 1)`);
    else if (info.canonicals[0].replace(/\/$/, "") !== info.location.replace(/\/$/, "")) issues.push(`canonical aponta para outra URL: ${info.canonicals[0]}`);
  }
  for (const p of ["og:title", "og:url", "og:image", "og:type"]) {
    if (!info.og[p].length) issues.push(`sem ${p} (previa do link no WhatsApp/redes sai pobre)`);
    else if (info.og[p].length > 1) issues.push(`${info.og[p].length} ${p} (duplicado)`);
  }
  if (desc && !info.og["og:description"].length) issues.push("sem og:description");
  if (info.og["og:url"][0] && info.canonicals[0] && info.og["og:url"][0].replace(/\/$/, "") !== info.canonicals[0].replace(/\/$/, "")) {
    issues.push("og:url diferente do canonical");
  }
  if (!info.twitter.length) notes.push("sem twitter:card");
  if (info.generator.length) issues.push(`meta generator revela a versao: ${info.generator[0]}`);
  const img = info.og["og:image"][0];
  if (img) {
    if (!/^https?:\/\//.test(img)) issues.push(`og:image relativa (${img}) - redes exigem URL absoluta`);
    else {
      try {
        const res = await page.request.get(img, { timeout: 20000 });
        const type = res.headers()["content-type"] || "";
        if (res.status() >= 400 || !type.startsWith("image/")) issues.push(`og:image nao abre (HTTP ${res.status()}, ${type || "sem tipo"})`);
        else {
          const dims = await page.evaluate((src) => new Promise((ok) => {
            const im = new Image(); im.onload = () => ok([im.naturalWidth, im.naturalHeight]); im.onerror = () => ok(null); im.src = src;
          }), img);
          if (dims && (dims[0] < 1200 || dims[1] < 630)) notes.push(`og:image ${dims[0]}x${dims[1]} (recomendado 1200x630)`);
        }
      } catch (err) {
        issues.push(`og:image falhou: ${String(err.message).split("\n")[0]}`);
      }
    }
  }
  // JSON-LD: valido, sem campo vazio; na Home, a empresa.
  const nodes = [];
  info.ld.forEach((raw, i) => {
    try {
      const data = JSON.parse(raw);
      for (const n of [].concat(data["@graph"] || data)) nodes.push(n);
    } catch {
      issues.push(`JSON-LD #${i + 1} invalido (o Google ignora o bloco inteiro)`);
    }
  });
  const empty = [];
  const walk = (v, path) => {
    if (v === "" || v === null || (Array.isArray(v) && !v.length)) empty.push(path);
    else if (typeof v === "object") for (const [k, x] of Object.entries(v)) walk(x, `${path}.${k}`);
  };
  nodes.forEach((n, i) => walk(n, n["@type"] || `#${i}`));
  if (empty.length) issues.push(`JSON-LD com campo vazio: ${empty.slice(0, 4).join(", ")}`);
  if (ctx.isHome && exp && exp.plugin === "none") {
    const typeOf = (n) => [].concat(n["@type"] || []);
    const org = nodes.find((n) => typeOf(n).some((t) => t !== "WebSite" && t !== "BreadcrumbList" && t !== "FAQPage" && n.name && n.url));
    if (!org) issues.push("Home sem dados estruturados da empresa (Organization/LocalBusiness)");
    else {
      if (exp.organization_type && !typeOf(org).includes(exp.organization_type)) issues.push(`empresa como ${typeOf(org).join("/")}, Blueprint diz ${exp.organization_type}`);
      if (exp.organization_type && exp.organization_type !== "Organization" && !org.address) issues.push(`${exp.organization_type} sem endereco (preencha o endereco em Configuracoes do Site)`);
    }
    if (!nodes.some((n) => typeOf(n).includes("WebSite"))) notes.push("sem WebSite no JSON-LD (nome do site no Google)");
  }
  // Icone do site e sinais basicos (references/site-icon.md) - so na Home.
  if (ctx.isHome) {
    if (!info.icons) issues.push("sem Icone do site (aba do navegador mostra o icone generico) - Aparencia > Personalizar > Identidade do site");
    else if (!info.apple) notes.push("sem apple-touch-icon");
    if (info.manifest) {
      try {
        const res = await page.request.get(info.manifest, { timeout: 15000 });
        const data = await res.json();
        if (!data.name || !(data.icons || []).length) issues.push("manifesto sem nome ou sem icones");
      } catch (err) {
        issues.push(`manifesto nao abre ou nao e JSON (${String(err.message).split("\n")[0].slice(0, 80)})`);
      }
    } else if (info.icons) notes.push("sem manifesto (site.webmanifest)");
    if (!info.themeColor) notes.push("sem meta theme-color (cor da barra do navegador no celular)");
    if (!info.feed) notes.push("sem link do feed RSS no <head> (automatic-feed-links)");
  }
  return { id: "seo", issues, notes, title: info.title, description: desc, noindex, canonical: info.canonicals[0] || null };
}

// Hero, cabecalho de pagina, faixa de chamada e aviso (references/hero-banners.md).
// O contraste do texto sobre a foto e medido de verdade: esconde o texto,
// fotografa o retangulo atras dele e o capture_site.py compara os pixels
// com a cor do texto (WCAG 1.4.3).
async function checkHero(page, exp, ctx) {
  const issues = [];
  const h1 = await page.evaluate(() => document.querySelectorAll("h1").length);
  if (h1 !== 1) issues.push(`${h1} <h1> na pagina (deve ser exatamente 1)`);
  const info = await page.evaluate(() => {
    const hero = document.querySelector("[data-hero], [data-page-header]");
    if (!hero) return null;
    const img = hero.querySelector("img");
    return {
      kind: hero.matches("[data-page-header]") ? "page_header" : "hero",
      img: img ? { loading: img.getAttribute("loading"), priority: img.getAttribute("fetchpriority") } : null,
      buttons: [...hero.querySelectorAll(".button")].map((b) => ({ text: b.textContent.replace(/\s+/g, " ").trim(), href: b.getAttribute("href") || "" })),
      crumbs: hero.querySelector("[data-breadcrumb]") ? {
        items: hero.querySelectorAll("[data-breadcrumb] li").length,
        current: !!hero.querySelector('[data-breadcrumb] li:last-child [aria-current="page"]'),
        ld: [...document.querySelectorAll('script[type="application/ld+json"]')].map((s) => { try { return JSON.parse(s.textContent); } catch { return {}; } })
          .filter((d) => d["@type"] === "BreadcrumbList").map((d) => (d.itemListElement || []).length)[0] ?? null,
      } : null,
    };
  });
  if (exp && !info) issues.push("hero/cabecalho de pagina ausente (data-hero / data-page-header)");
  if (info) {
    if (info.img) {
      if (info.img.loading === "lazy") issues.push("imagem do hero com loading=lazy (e o LCP)");
      if (info.img.priority !== "high") issues.push("imagem do hero sem fetchpriority=high");
      const lcp = await page.evaluate(() => new Promise((resolve) => {
        new PerformanceObserver((list) => {
          const e = list.getEntries().at(-1);
          resolve(e && e.element ? (e.element.closest("[data-hero], [data-page-header]") ? "hero" : `${e.element.tagName.toLowerCase()}.${e.element.className}`) : null);
        }).observe({ type: "largest-contentful-paint", buffered: true });
        setTimeout(() => resolve(null), 1500);
      }));
      if (lcp && lcp !== "hero") issues.push(`o LCP da pagina nao e o hero (e ${lcp})`);
    }
    const want = (exp && exp.buttons) || [];
    if (want.length && info.buttons.map((b) => b.text).join("|") !== want.join("|")) issues.push(`botoes [${info.buttons.map((b) => b.text).join(", ")}] (referencia: [${want.join(", ")}])`);
    info.buttons.filter((b) => !b.href || b.href === "#").forEach((b) => issues.push(`botao "${b.text}" sem destino`));
    if (exp && exp.breadcrumb === true) {
      if (!info.crumbs) issues.push("sem trilha de navegacao (breadcrumb)");
      else {
        if (!info.crumbs.current) issues.push("trilha sem a pagina atual marcada (aria-current)");
        if (info.crumbs.ld !== info.crumbs.items) issues.push("trilha sem JSON-LD BreadcrumbList com os mesmos itens");
      }
    }
  }
  // Contraste: texto marcado com data-contrast dentro de hero, cabecalho e faixa.
  // Botoes tambem: escondendo so o TEXTO, o recorte traz o fundo do botao
  // (se houver) - vale para botao cheio e para botao so com contorno.
  const targets = await page.evaluate(() => [...document.querySelectorAll("[data-hero] [data-contrast], [data-page-header] [data-contrast], [data-cta-band] [data-contrast], [data-hero] .button, [data-cta-band] .button")]
    .filter((el) => el.closest("[data-hero], [data-page-header], [data-cta-band]").querySelector("img"))
    .map((el, i) => { el.dataset.contrastIdx = String(i); const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
      return { idx: i, label: (el.textContent || "").trim().slice(0, 30), color: s.color, size: parseFloat(s.fontSize), weight: parseInt(s.fontWeight, 10),
        rect: { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: r.height } }; }));
  const contrast = [];
  if (targets.length) {
    await page.addStyleTag({ content: "[data-contrast]{visibility:hidden!important} [data-hero] .button,[data-cta-band] .button{color:transparent!important;text-shadow:none!important}" });
    for (const t of targets) {
      if (t.rect.width < 2 || t.rect.height < 2) continue;
      const file = `contrast-${ctx.page}-${ctx.viewport}-${t.idx}.png`;
      await page.screenshot({ path: join(config.out, file), clip: t.rect, fullPage: true });
      contrast.push({ ...t, file });
    }
    await page.evaluate(() => document.querySelectorAll("style").forEach((s) => { if (s.textContent.includes("[data-contrast]{visibility:hidden")) s.remove(); }));
  }
  // Barra de aviso fechavel: fecha e continua fechada depois de recarregar.
  if (ctx.announcement && ctx.viewport === "desktop" && ctx.isHome) {
    const bar = page.locator("[data-announcement]");
    if (!(await bar.count())) issues.push("barra de aviso ausente");
    else if (ctx.announcement.dismissible) {
      const btn = bar.locator("[data-announcement-close]");
      if (!(await btn.isVisible().catch(() => false))) issues.push("aviso sem botao de fechar visivel");
      else {
        if (!(await btn.textContent()).trim()) issues.push("botao de fechar o aviso sem nome acessivel");
        await btn.click();
        await page.reload({ waitUntil: "networkidle" });
        if (await page.locator("[data-announcement]").isVisible()) issues.push("aviso volta a aparecer depois de fechado");
        await page.evaluate(() => localStorage.clear());
      }
    }
  }
  return { id: "hero", issues, contrast };
}

async function runAxe(page) {
  await page.addScriptTag({ path: axePath });
  const result = await page.evaluate(async () =>
    // eslint-disable-next-line no-undef
    axe.run(document, { runOnly: { type: "tag", values: ["wcag2a", "wcag2aa"] } })
  );
  return result.violations.map((v) => ({
    id: v.id,
    impact: v.impact,
    help: v.help,
    nodes: v.nodes.length,
    example: v.nodes[0]?.target?.join(" ") ?? "",
  }));
}

const browser = await chromium.launch();
const report = { base: config.base, generatedAt: new Date().toISOString(), captures: [], brokenLinks: [], errors: [] };
const allLinks = new Set();

try {
  for (const vp of config.viewports) {
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      deviceScaleFactor: 1,
      reducedMotion: "reduce",
    });
    // CLS desde a primeira pintura (antes do FREEZE_CSS e da rolagem do QA).
    await context.addInitScript(CLS_OBSERVER);
    for (const pg of config.pages) {
      const page = await context.newPage();
      const consoleErrors = [];
      const httpErrors = [];
      page.on("console", (msg) => { if (msg.type() === "error") consoleErrors.push(msg.text()); });
      page.on("pageerror", (err) => consoleErrors.push(`[pageerror] ${err.message}`));
      page.on("response", (res) => { if (res.status() >= 400) httpErrors.push(`${res.status()} ${res.url()}`); });
      page.on("requestfailed", (req) => httpErrors.push(`FAILED ${req.url()} (${req.failure()?.errorText})`));

      const url = pageUrl(pg.path);
      const entry = { page: pg.id, path: pg.path, url, viewport: vp.name, width: vp.width };
      try {
        const res = await page.goto(url, { waitUntil: "networkidle", timeout: 45000 });
        entry.status = res ? res.status() : null;
        await page.waitForTimeout(400);
        const shifts = await page.evaluate(() => ({ cls: window.__qaCls || 0, sources: window.__qaShifts || [] }));
        entry.layout_shift = [{ id: "cls", cls: Number(shifts.cls.toFixed(4)), sources: shifts.sources.slice(0, 5),
          issues: shifts.cls > 0.1 ? [`CLS ${shifts.cls.toFixed(3)} ao carregar (acima de 0,1 o Google considera ruim) - maiores saltos: ${shifts.sources.slice(0, 3).map((s) => `${s.v.toFixed(3)} em ${s.src.join(" ") || "?"}`).join("; ")}`] : [] }];
        if (vp.name === config.viewports[0].name) entry.fonts = [await checkFonts(page, config.fonts ?? null)];
        entry.performance = [await measurePerformance(page)];
        await page.addStyleTag({ content: FREEZE_CSS });
        await autoScroll(page);
        entry.images = [await checkImages(page)];
        Object.assign(entry, await inspect(page));
        entry.links.forEach((l) => allLinks.add(l));
        delete entry.links;
        entry.screenshot = `${pg.id}-${vp.name}.png`;
        await page.screenshot({ path: join(config.out, entry.screenshot), fullPage: true });
        if (config.axe && AXE_VIEWPORTS.has(vp.name)) entry.axe = await runAxe(page);
        entry.navigation = await checkNavigation(page, !!config.stickyHeader);
        entry.carousels = await checkCarousels(page, pg.carousels ?? null);
        // Envio de formulario so uma vez por pagina (desktop): gera e-mail/registro.
        entry.forms = await checkForms(page, pg.forms ?? null, !!config.submitForms && vp.name === "desktop");
        entry.maps = await checkMaps(page, pg.maps ?? null);
        entry.galleries = await checkGalleries(page, pg.galleries ?? null);
        entry.videos = await checkVideos(page, pg.videos ?? null, vp.name);
        const heroCheck = await checkHero(page, pg.hero ?? null, { page: pg.id, viewport: vp.name, isHome: pg.path === "/", announcement: config.announcement ?? null });
        entry.hero = [heroCheck];
        // O <head> e igual em todo viewport: SEO so no primeiro.
        if (vp.name === config.viewports[0].name) {
          entry.seo = [await checkSeo(page, { ...(config.seo ?? { plugin: "none" }), ...(pg.seo ?? {}) }, { isHome: pg.path === "/" })];
        }
        const headerCheck = await checkHeader(page, config.header ?? null, vp.name, pg.path === "/");
        entry.header = headerCheck ? [headerCheck] : [];
        const footerCheck = await checkFooter(page, config.footer ?? null, pg.path === "/");
        entry.footer = footerCheck ? [footerCheck] : [];
        const blog = await checkBlog(page, config.blog ?? null);
        entry.blog = blog ? [blog] : [];
        entry.team = await checkTeam(page, pg.team ?? null);
        entry.stats = await checkStats(page, pg.stats ?? null);
        entry.testimonials = await checkTestimonials(page, pg.testimonials ?? null);
        entry.client_logos = await checkClientLogos(page, pg.client_logos ?? null);
        entry.tables = await checkTables(page, pg.tables ?? null, vp.name);
        entry.pricing = await checkPricing(page, pg.pricing ?? null);
        entry.tabs = await checkTabs(page, pg.tabs ?? null, vp.name);
        entry.accordions = await checkAccordions(page, pg.accordions ?? null, vp.name);
      } catch (err) {
        entry.captureError = String(err.message || err).split("\n")[0];
      }
      entry.consoleErrors = consoleErrors;
      entry.httpErrors = [...new Set(httpErrors)];
      report.captures.push(entry);
      console.log(`${entry.captureError ? "ERRO" : "ok  "} ${pg.id} @ ${vp.name} (${vp.width}px)${entry.captureError ? " - " + entry.captureError : ""}`);
      await page.close();
    }
    await context.close();
  }

  // Troca de fonte: a mesma pagina com os arquivos de fonte bloqueados (so a
  // reserva) e com eles carregados - quanto o texto se move na troca.
  const swapPage = config.pages.find((p) => p.path === "/") || config.pages[0];
  if (swapPage && config.fonts && config.fonts.delivery !== "system") {
    report.fontSwap = [];
    for (const vp of [config.viewports[0], config.viewports[config.viewports.length - 1]].filter((v, i, a) => a.indexOf(v) === i)) {
      try {
        report.fontSwap.push({ page: swapPage.id, viewport: vp.name, ...(await measureFontSwap(browser, pageUrl(swapPage.path), vp)) });
      } catch (err) {
        report.fontSwap.push({ page: swapPage.id, viewport: vp.name, error: String(err.message).split("\n")[0] });
      }
    }
  }

  if (config.checkLinks && allLinks.size) {
    const ctx = await browser.newContext();
    const links = [...allLinks].slice(0, config.maxLinks || 200);
    for (const link of links) {
      try {
        const res = await ctx.request.get(link, { maxRedirects: 5, timeout: 20000 });
        if (res.status() >= 400) report.brokenLinks.push(`${res.status()} ${link}`);
      } catch (err) {
        report.brokenLinks.push(`FAILED ${link} (${String(err.message).split("\n")[0]})`);
      }
    }
    report.linksChecked = links.length;
    await ctx.close();
  }
} catch (err) {
  report.errors.push(String(err.stack || err));
} finally {
  await browser.close();
}

writeFileSync(join(config.out, "report.json"), JSON.stringify(report, null, 2));
