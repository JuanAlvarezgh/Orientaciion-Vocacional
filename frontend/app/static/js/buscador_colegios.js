// Buscador de colegios con autocompletar (patrón combobox de WAI-ARIA).
// Uso: BuscadorColegios.iniciar(raiz), donde raiz contiene:
//   input[data-colegio-buscar], ul[data-colegio-lista], input[name=sede_codigo],
//   y opcionalmente select[data-colegio-municipio] para filtrar.
window.BuscadorColegios = (function () {
  function escapar(t) {
    return String(t ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  function iniciar(raiz, alElegir) {
    const entrada = raiz.querySelector('[data-colegio-buscar]');
    const lista = raiz.querySelector('[data-colegio-lista]');
    const codigo = raiz.querySelector('input[name="sede_codigo"]');
    const municipio = raiz.querySelector('[data-colegio-municipio]');
    let resultados = [];
    let activo = -1;
    let espera;

    function cerrar() {
      lista.hidden = true;
      entrada.setAttribute('aria-expanded', 'false');
      activo = -1;
    }

    function pintar() {
      if (!resultados.length) {
        lista.innerHTML = '<li class="bc-vacio">No aparece. Revisa el nombre o marca "Mi colegio no aparece".</li>';
      } else {
        lista.innerHTML = resultados.map((c, i) => `
          <li role="option" id="bc-op-${i}" class="bc-op${i === activo ? ' activo' : ''}" data-i="${i}" aria-selected="${i === activo}">
            <span class="bc-nombre">${escapar(c.nombre)}</span>
            <span class="bc-detalle">${escapar(c.sede && c.sede !== c.nombre ? c.sede + ' · ' : '')}${escapar(c.sector)} · ${escapar(c.municipio.charAt(0) + c.municipio.slice(1).toLowerCase())}</span>
          </li>`).join('');
      }
      lista.hidden = false;
      entrada.setAttribute('aria-expanded', 'true');
      entrada.setAttribute('aria-activedescendant', activo >= 0 ? `bc-op-${activo}` : '');
    }

    function elegir(i) {
      const c = resultados[i];
      if (!c) return;
      entrada.value = c.nombre_visible;
      codigo.value = c.codigo;
      cerrar();
      if (alElegir) alElegir(c);
    }

    async function buscar() {
      const q = entrada.value.trim();
      codigo.value = '';
      if (q.length < 2) { cerrar(); return; }
      const params = new URLSearchParams({ q });
      if (municipio && municipio.value) params.set('municipio', municipio.value);
      try {
        const r = await fetch('/api/colegios?' + params);
        resultados = r.ok ? (await r.json()).colegios || [] : [];
      } catch (e) {
        resultados = [];
      }
      activo = -1;
      pintar();
    }

    entrada.addEventListener('input', () => { clearTimeout(espera); espera = setTimeout(buscar, 180); });
    entrada.addEventListener('keydown', (e) => {
      if (lista.hidden) return;
      if (e.key === 'ArrowDown') { activo = Math.min(activo + 1, resultados.length - 1); pintar(); e.preventDefault(); }
      else if (e.key === 'ArrowUp') { activo = Math.max(activo - 1, 0); pintar(); e.preventDefault(); }
      else if (e.key === 'Enter' && activo >= 0) { elegir(activo); e.preventDefault(); }
      else if (e.key === 'Escape') { cerrar(); }
    });
    lista.addEventListener('mousedown', (e) => {
      const op = e.target.closest('[data-i]');
      if (op) { elegir(Number(op.dataset.i)); e.preventDefault(); }
    });
    entrada.addEventListener('blur', () => setTimeout(cerrar, 120));
    if (municipio) municipio.addEventListener('change', () => { if (entrada.value.trim().length >= 2) buscar(); });
  }

  return { iniciar };
})();
