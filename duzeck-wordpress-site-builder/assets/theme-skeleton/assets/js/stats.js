/**
 * Contagem dos numeros em destaque (template-parts/stats.php,
 * references/team-stats.md). So a copia VISUAL (aria-hidden) anima; o
 * valor final ja esta no HTML para leitor de tela, buscador e sem JS.
 * Uma vez por numero, ao entrar na tela; nada com prefers-reduced-motion.
 * Estado para o QA: data-animated (pending | running | done) em cada numero.
 */
(function () {
    'use strict';

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || !('IntersectionObserver' in window)) {
        return;
    }

    var DURATION = 1600;

    function format(value, decimals) {
        return value.toLocaleString('pt-BR', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
    }

    function animate(el) {
        var target = parseFloat(el.dataset.countTo);
        var decimals = parseInt(el.dataset.decimals, 10) || 0;
        var prefix = el.dataset.prefix || '';
        var suffix = el.dataset.suffix || '';
        var final = el.dataset.final; // guardado ANTES de zerar (abaixo)
        var start = null;
        el.dataset.animated = 'running';

        function frame(now) {
            if (start === null) { start = now; }
            var t = Math.min(1, (now - start) / DURATION);
            var eased = 1 - Math.pow(1 - t, 3); // desacelera no fim
            el.textContent = prefix + format(target * eased, decimals) + suffix;
            if (t < 1) {
                requestAnimationFrame(frame);
            } else {
                el.textContent = final; // exatamente o texto do servidor
                el.dataset.animated = 'done';
            }
        }
        requestAnimationFrame(frame);
    }

    var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                observer.unobserve(entry.target);
                animate(entry.target);
            }
        });
    }, { threshold: 0.6 });

    document.querySelectorAll('[data-stats][data-count-up="true"] [data-count-to]').forEach(function (el) {
        var target = parseFloat(el.dataset.countTo);
        if (!isFinite(target)) { return; }
        el.dataset.animated = 'pending';
        el.dataset.final = el.textContent; // texto exato do servidor, restaurado no fim
        // Largura REAL do valor final (o min-width em ch do HTML nao cobre "+", "%", "m²"):
        // a contagem nunca empurra o layout.
        el.style.minWidth = el.getBoundingClientRect().width + 'px';
        el.textContent = (el.dataset.prefix || '') + format(0, parseInt(el.dataset.decimals, 10) || 0) + (el.dataset.suffix || '');
        observer.observe(el);
    });
})();
