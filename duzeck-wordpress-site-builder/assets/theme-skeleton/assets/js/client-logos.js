/**
 * Faixa de logos que rola sem parar (template-parts/client-logos.php,
 * layout marquee - references/social-proof.md).
 *
 * Sem JS: fileira parada (nada se move sem botao de pausa).
 * Com JS: duplica a lista para o loop continuo - a copia e aria-hidden e
 * inert (leitor de tela e Tab encontram cada empresa uma vez so) -, liga
 * a animacao (CSS) e mostra o botao de pausa/reproduzir (WCAG 2.2.2).
 * Para tambem com o mouse em cima e com foco dentro (CSS). Com
 * prefers-reduced-motion a animacao nao roda (CSS) e o botao some.
 * Estado para o QA: data-paused no [data-client-logos].
 */
(function () {
    'use strict';

    var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

    document.querySelectorAll('.client-logos--marquee').forEach(function (root) {
        var track = root.querySelector('[data-logos-track]');
        var list = track && track.querySelector('.client-logos__list');
        var toggle = root.querySelector('[data-logos-toggle]');
        var label = root.querySelector('[data-logos-toggle-label]');
        if (!list) {
            return;
        }

        var copy = list.cloneNode(true);
        copy.setAttribute('aria-hidden', 'true');
        copy.inert = true;
        copy.classList.add('client-logos__list--clone');
        track.appendChild(copy);

        // Velocidade constante (~40px/s), qualquer que seja a quantidade de logos.
        root.style.setProperty('--marquee-duration', Math.max(15, Math.round(list.scrollWidth / 40)) + 's');

        var paused = false;
        function render() {
            root.classList.toggle('is-paused', paused);
            root.dataset.paused = String(paused || reduceMotion.matches);
            if (toggle) {
                toggle.hidden = reduceMotion.matches;
                toggle.setAttribute('data-state', paused ? 'paused' : 'playing');
                if (label) {
                    label.textContent = paused ? root.dataset.labelPlay : root.dataset.labelPause;
                }
            }
        }
        if (toggle) {
            toggle.addEventListener('click', function () {
                paused = !paused;
                render();
            });
        }
        reduceMotion.addEventListener('change', render);
        root.classList.add('client-logos--js');
        render();
    });
})();
