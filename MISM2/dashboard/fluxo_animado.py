"""Mapa animado do fluxo de mulheres de uma cidade: para onde vão as moradoras e de onde vêm as mulheres de fora.

A cidade escolhida fica no centro; cada cidade de destino ou de origem aparece na direção real em que está, com a distância encolhida
(escala logarítmica) para caber todas na tela. Pontinhos correm pelas linhas: laranja para quem sai, lilás para quem chega; a quantidade de
pontos e o tamanho da bolha acompanham o número de internações. Só descreve: conta internações, não pessoas, e não explica por quê.
O ponto de cada cidade é o centro do município (nunca um endereço). Sem posição conhecida a cidade fica de fora. Quem tem
`prefers-reduced-motion` vê o desenho parado. O desenho é HTML puro (canvas), sem biblioteca nem mapa de fundo.
"""
import json
import math

import entendimento as ent
import localizacao as loc

MINIMO_SAIDA = 3      # destinos com menos internações que isto não entram (ruído)
MINIMO_ENTRADA = 5    # origens com menos internações que isto não entram
MAXIMO_POR_LADO = 9   # no máximo tantas cidades de cada lado, as maiores

PAINEL = """<div id="wrap" style="position:relative;width:100%;height:560px;background:#231028;border-radius:18px;overflow:hidden;font-family:'DM Sans',system-ui,sans-serif">
<canvas id="c" style="display:block;width:100%;height:100%"></canvas>
<div id="leg" style="position:absolute;left:16px;bottom:14px;color:#e8dcef;font-size:13px;line-height:1.7">
 <div><span style="display:inline-block;width:11px;height:11px;border-radius:50%;background:#ff8a4c;margin-right:8px"></span><span id="l1"></span></div>
 <div><span style="display:inline-block;width:11px;height:11px;border-radius:50%;background:#d7b4ff;margin-right:8px"></span><span id="l2"></span></div>
 <div style="opacity:.65">o tamanho da bolha e a quantidade de pontos são o número de internações</div></div>
<div id="tip" style="position:absolute;pointer-events:none;display:none;background:#fff;color:#2a1730;border-radius:10px;padding:8px 12px;font-size:13px;line-height:1.45;box-shadow:0 6px 20px rgba(0,0,0,.35);max-width:240px"></div></div>
<script>
const D = __DADOS__;
const cv = document.getElementById('c'), cx = cv.getContext('2d'), wrap = document.getElementById('wrap'), tip = document.getElementById('tip');
document.getElementById('l1').textContent = 'moradoras de ' + D.centro.nome + ' que se trataram em outra cidade';
document.getElementById('l2').textContent = 'mulheres de outras cidades atendidas em ' + D.centro.nome;
const parado = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
const COR_SAI = '#ff8a4c', COR_ENT = '#d7b4ff';
let W = 0, H = 0, nos = [], fluxos = [], raio = () => 0;
function fmt(n) { return n.toLocaleString('pt-BR'); }
function montar() {
  const r = wrap.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
  W = r.width; H = r.height; cv.width = W * dpr; cv.height = H * dpr; cx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const cxm = W / 2, cym = H / 2 - 6, rmax = Math.min(W / 2, H / 2) - 62, r0 = 80, kmax = Math.max(...D.cidades.map(c => c.km), 30);
  raio = km => r0 + (rmax - r0) * Math.log(1 + km / 8) / Math.log(1 + kmax / 8);
  nos = D.cidades.map(c => ({...c, x: cxm + raio(c.km) * Math.cos(c.ang), y: cym - raio(c.km) * Math.sin(c.ang),
                              r: 5 + 1.9 * Math.sqrt(c.sai + c.ent)}));
  for (let it = 0; it < 80; it++) for (let i = 0; i < nos.length; i++) for (let j = i + 1; j < nos.length; j++) {   // afasta quem ficou colado
    const a = nos[i], b = nos[j], dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 1, min = a.r + b.r + 30;
    if (d < min) { const f = (min - d) / 2 / d; a.x -= dx * f; a.y -= dy * f; b.x += dx * f; b.y += dy * f; }
  }
  nos.forEach(n => { n.x = Math.max(n.r + 8, Math.min(W - n.r - 8, n.x)); n.y = Math.max(n.r + 8, Math.min(H - n.r - 70, n.y)); });
  const c = {x: cxm, y: cym}; D.centro.x = c.x; D.centro.y = c.y;
  fluxos = [];
  nos.forEach(n => {
    [['sai', COR_SAI], ['ent', COR_ENT]].forEach(([tipo, cor], k) => {
      if (!n[tipo]) return;
      const sx = tipo === 'sai' ? c.x : n.x, sy = tipo === 'sai' ? c.y : n.y, ex = tipo === 'sai' ? n.x : c.x, ey = tipo === 'sai' ? n.y : c.y;
      const mx = (sx + ex) / 2, my = (sy + ey) / 2, nx = -(ey - sy), ny = (ex - sx), len = Math.hypot(nx, ny) || 1, curva = (k ? -1 : 1) * 0.16;
      const pts = Math.max(2, Math.min(18, Math.round(n[tipo] / 6)));
      fluxos.push({cor, sx, sy, ex, ey, qx: mx + nx / len * len * curva, qy: my + ny / len * len * curva, n: n[tipo],
                   particulas: Array.from({length: pts}, (_, i) => ({t: i / pts, v: 0.0022 + 0.0016 * ((i * 7) % 5) / 4}))});
    });
  });
}
function bez(f, t) { const u = 1 - t; return [u * u * f.sx + 2 * u * t * f.qx + t * t * f.ex, u * u * f.sy + 2 * u * t * f.qy + t * t * f.ey]; }
function desenhar() {
  cx.clearRect(0, 0, W, H);
  const c = D.centro;
  [10, 50, 150].forEach(km => { const r = raio(km); if (r > 70 && r < Math.min(W, H) / 2) {
    cx.beginPath(); cx.arc(c.x, c.y, r, 0, 7); cx.strokeStyle = 'rgba(255,255,255,.07)'; cx.lineWidth = 1; cx.stroke();
    cx.fillStyle = 'rgba(255,255,255,.28)'; cx.font = '11px sans-serif'; cx.fillText(km + ' km', c.x + r * 0.72 + 4, c.y - r * 0.72 - 3); } });
  fluxos.forEach(f => {                                                   // linhas finas (a espessura acompanha o volume)
    cx.beginPath(); cx.moveTo(f.sx, f.sy); cx.quadraticCurveTo(f.qx, f.qy, f.ex, f.ey);
    cx.strokeStyle = f.cor; cx.globalAlpha = 0.22; cx.lineWidth = 0.8 + Math.sqrt(f.n) * 0.28; cx.stroke(); cx.globalAlpha = 1;
  });
  cx.globalCompositeOperation = 'lighter';
  fluxos.forEach(f => f.particulas.forEach(p => {
    if (!parado) p.t = (p.t + p.v) % 1;
    for (let k = 0; k < 6; k++) { const [x, y] = bez(f, Math.max(0, p.t - k * 0.012));                // pontinho com rastro
      cx.beginPath(); cx.arc(x, y, 3.1 - k * 0.38, 0, 7); cx.fillStyle = f.cor; cx.globalAlpha = 0.9 - k * 0.14; cx.fill(); }
    cx.globalAlpha = 1;
  }));
  cx.globalCompositeOperation = 'source-over';
  nos.forEach(n => {
    cx.beginPath(); cx.arc(n.x, n.y, n.r, 0, 7); cx.fillStyle = 'rgba(35,16,40,.9)'; cx.fill();
    cx.lineWidth = 2.5; cx.strokeStyle = n.sai >= n.ent ? COR_SAI : COR_ENT; cx.stroke();
    cx.fillStyle = '#fff'; cx.font = '600 13px DM Sans, sans-serif'; cx.textAlign = 'center';
    cx.fillText(n.nome, n.x, n.y + n.r + 15); cx.font = '12px DM Sans, sans-serif'; cx.fillStyle = 'rgba(255,255,255,.7)';
    cx.fillText(fmt(n.sai + n.ent), n.x, n.y + n.r + 29);
  });
  const partes = D.centro.nome.split(' '), linhas = partes.length > 1 ? [partes[0], partes.slice(1).join(' ')] : [D.centro.nome];
  cx.beginPath(); cx.arc(c.x, c.y, 34, 0, 7); cx.fillStyle = '#5b2a55'; cx.fill(); cx.lineWidth = 3; cx.strokeStyle = '#fff'; cx.stroke();
  cx.fillStyle = '#fff'; cx.font = (D.centro.nome.length > 14 ? '700 11px' : '700 13px') + ' DM Sans, sans-serif';
  linhas.forEach((t, i) => cx.fillText(t, c.x, c.y + (linhas.length === 1 ? 4 : (i ? 14 : -1))));
  if (!parado) requestAnimationFrame(desenhar);
}
cv.addEventListener('mousemove', e => {
  const r = cv.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
  const n = nos.find(n => Math.hypot(n.x - x, n.y - y) < n.r + 8);
  if (!n) { tip.style.display = 'none'; return; }
  tip.innerHTML = '<b>' + n.nome + '</b>' + (n.sai ? '<br>' + fmt(n.sai) + ' internações de moradoras de ' + D.centro.nome + ' foram aqui' : '')
    + (n.ent ? '<br>' + fmt(n.ent) + ' internações de mulheres de ' + n.nome + ' foram em ' + D.centro.nome : '');
  tip.style.display = 'block'; tip.style.left = Math.min(x + 14, W - 250) + 'px'; tip.style.top = Math.max(y - 20, 4) + 'px';
});
cv.addEventListener('mouseleave', () => tip.style.display = 'none');
new ResizeObserver(() => { montar(); if (parado) desenhar(); }).observe(wrap);
montar(); desenhar();
</script>"""


def dados_do_fluxo(info, posicoes, nome_cidade):
    """Cidades (com direção e distância a partir de `nome_cidade`) para onde as moradoras vão e de onde vêm as mulheres de fora.

    `info`: o que `inteligencia.fluxo_da_cidade` devolve (destinos e origens). `posicoes`: `localizacao.carregar_localizacao`.
    Devolve None se faltar o fluxo, a tabela de posições ou o centro da cidade (nunca inventa um ponto)."""
    if not info or posicoes is None or len(posicoes) == 0:
        return None
    centro = loc._ponto(posicoes, ent.normalizar(nome_cidade))
    if centro is None:
        return None
    cidades = {}
    for nome, n in list(info.get("destinos") or [])[:MAXIMO_POR_LADO]:
        if n >= MINIMO_SAIDA:
            cidades.setdefault(nome, {"nome": nome, "sai": 0, "ent": 0})["sai"] += int(n)
    for o in list(info.get("origens") or [])[:MAXIMO_POR_LADO]:
        if o["internacoes"] >= MINIMO_ENTRADA:
            cidades.setdefault(o["nome"], {"nome": o["nome"], "sai": 0, "ent": 0})["ent"] += int(o["internacoes"])
    saida = []
    for c in cidades.values():
        p = loc._ponto(posicoes, ent.normalizar(c["nome"]))
        if p is None:
            continue
        dx, dy = (p[1] - centro[1]) * math.cos(math.radians(centro[0])) * 111.32, (p[0] - centro[0]) * 110.57
        c.update(km=round(math.hypot(dx, dy), 1), ang=round(math.atan2(dy, dx), 4))
        saida.append(c)
    return {"centro": {"nome": nome_cidade}, "cidades": saida} if saida else None


def html_do_fluxo(dados):
    """HTML pronto para `components.html(..., height=580)`. Os dados vão como JSON (com `</` escapado)."""
    return PAINEL.replace("__DADOS__", json.dumps(dados, ensure_ascii=False).replace("</", "<\\/"))
