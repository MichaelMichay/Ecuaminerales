var DATA = JSON.parse(document.getElementById('catalogo-data').textContent);
var CAT = {}, P = [];
var R = {}, IMC = {}; DATA.categorias.forEach(function (c) { CAT[c.nombre] = c.color; R[c.nombre] = c.resumen || ''; IMC[c.nombre] = c.imagen || '' });

DATA.productos.forEach(function (p) { P.push([p.nombre, p.categoria, p.descripcion, p.detalle || '', !!p.agotado, p.imagen || '']) });
function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c] }) }
var cur = 'Todos', $ = function (i) { return document.getElementById(i) };
function gem(c) { return '<svg viewBox="0 0 64 64"><path d="M32 4l22 18-22 38L10 22z" fill="' + c + '"/><path d="M32 4l10 18H22z" fill="#fff" opacity=".45"/><path d="M32 60L22 22h20z" fill="#000" opacity=".12"/></svg>' }
/* carrusel (las diapositivas las genera Django) */
var N = $('tr').children.length, n = 0, tm;
if (N > 1) { $('dots').innerHTML = [].map.call($('tr').children, function (_, i) { return '<button aria-label="Ir al comunicado ' + (i + 1) + '" data-i="' + i + '"></button>' }).join('') }
else { $('prev').style.display = 'none'; $('next').style.display = 'none' }
function go(i) { n = (i + N) % N; $('tr').style.transform = 'translateX(-' + n * 100 + '%)';[].forEach.call($('dots').children, function (b, k) { b.setAttribute('aria-current', k === n) }) }
function auto() { clearInterval(tm); if (N > 1 && !matchMedia('(prefers-reduced-motion:reduce)').matches) tm = setInterval(function () { go(n + 1) }, 6000) }
$('prev').onclick = function () { go(n - 1); auto() }; $('next').onclick = function () { go(n + 1); auto() };
$('dots').onclick = function (e) { if (e.target.dataset.i) { go(+e.target.dataset.i); auto() } };
$('comunicados').onmouseenter = function () { clearInterval(tm) }; $('comunicados').onmouseleave = auto;
go(0); auto();
/* categorías y productos */
var names = DATA.categorias.map(function (c) { return c.nombre });
$('cats').innerHTML = names.map(function (c) { var k = P.filter(function (p) { return p[1] === c }).length; return '<button class="cat" data-c="' + esc(c) + '">' + (IMC[c] ? '<img class="cat-img" src="' + esc(IMC[c]) + '" alt="" loading="lazy">' : gem(CAT[c])) + '<b>' + esc(c) + '</b>' + (R[c] || k ? '<small>' + esc(R[c] || k + ' producto' + (k > 1 ? 's' : '')) + '</small>' : '') + '</button>' }).join('');
$('tabs').innerHTML = ['Todos'].concat(names).map(function (c) { return '<button class="tab" role="tab" data-c="' + esc(c) + '">' + esc(c) + '</button>' }).join('');
function draw() {
    var q = $('q').value.trim().toLowerCase();
    var L = P.filter(function (p) { return (cur === 'Todos' || p[1] === cur) && (!q || (p[0] + ' ' + p[2]).toLowerCase().indexOf(q) > -1) });
    [].forEach.call($('tabs').children, function (b) { b.setAttribute('aria-selected', b.dataset.c === cur) });
    $('res').textContent = L.length + ' producto' + (L.length === 1 ? '' : 's') + (cur === 'Todos' ? '' : ' en ' + cur);
    $('grid').innerHTML = L.length ? L.map(function (p) { return '<article class="card"><div class="im" style="background:' + esc(CAT[p[1]]) + '1F">' + (p[5] ? '<img class="foto" src="' + esc(p[5]) + '" alt="' + esc(p[0]) + '" loading="lazy">' : gem(CAT[p[1]])) + '</div><div class="b"><span class="l">' + esc(p[1]) + '</span><h3>' + esc(p[0]) + '</h3><p>' + esc(p[2]) + '</p>' + (p[3] ? '<p class="stk' + (p[4] ? ' ago' : '') + '">' + esc(p[3]) + '</p>' : '') + '<a href="#contacto">Solicitar información →</a></div></article>' }).join('') : '<p class="vacio">' + (P.length ? 'No hay productos que coincidan con la búsqueda.' : 'Pronto publicaremos nuestro catálogo.') + '</p>';
}
function pick(e) { if (!P.length) return; var b = e.target.closest('[data-c]'); if (!b) return; cur = b.dataset.c; draw(); if (b.classList.contains('cat')) $('productos').scrollIntoView({ behavior: 'smooth' }) }
$('cats').onclick = pick; $('tabs').onclick = pick; $('q').oninput = draw; draw();
if (!P.length) { $('productos').style.display = 'none'; var bq = document.querySelector('.search'); if (bq) bq.style.display = 'none';[].forEach.call(document.querySelectorAll('.cat'), function (b) { b.style.cursor = 'default' }) }