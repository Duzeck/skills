/**
 * Mapa com fachada (template-parts/map.php, references/maps.md).
 * O link "Carregar mapa" funciona sozinho (abre o mapa numa nova aba); com
 * JS ele troca a fachada pelo iframe do provedor NA PAGINA, so no clique -
 * nenhum script/cookie de terceiro antes do visitante pedir.
 */
(function () {
    'use strict';

    document.addEventListener('click', function (event) {
        var trigger = event.target.closest('[data-map-load]');
        if (!trigger || event.ctrlKey || event.metaKey || event.shiftKey || event.button !== 0) {
            return; // ctrl/cmd+clique: deixa abrir em nova aba normalmente
        }
        var map = trigger.closest('[data-map]');
        var facade = map && map.querySelector('[data-map-facade]');
        var src = trigger.getAttribute('data-map-src');
        if (!facade || !src) {
            return;
        }
        event.preventDefault();

        var iframe = document.createElement('iframe');
        iframe.className = 'map__iframe';
        iframe.src = src;
        iframe.title = trigger.getAttribute('data-map-title') || '';
        iframe.loading = 'lazy';
        iframe.referrerPolicy = 'no-referrer-when-downgrade';
        iframe.allowFullscreen = true;

        facade.replaceWith(iframe);
        map.setAttribute('data-map-loaded', 'true');
        // Quem acionou pelo teclado continua no mesmo ponto: o foco vai para o mapa.
        iframe.focus();
    });
})();
