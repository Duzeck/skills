/**
 * Videos (template-parts/video.php, references/videos.md). Sem dependencias.
 *
 *  - Fachada (embed): o clique troca a capa pelo player do provedor na
 *    pagina (sem cookie/script de terceiro antes do clique). Ctrl/Cmd+clique
 *    abre o video no provedor normalmente.
 *  - Video de fundo: so toca se nao ha prefers-reduced-motion, nem economia
 *    de dados, e a tela tem >= 768px; so entao o arquivo e baixado. Pausa
 *    fora da tela; botao de pausa/play (WCAG 2.2.2). Com movimento reduzido
 *    comeca PAUSADO e o visitante pode dar play. No celular fica a capa.
 *    Estado para o QA: data-playing no [data-video].
 */
(function () {
    'use strict';

    /* Fachada ------------------------------------------------------------ */
    document.addEventListener('click', function (event) {
        var trigger = event.target.closest('[data-video-load]');
        if (!trigger || event.ctrlKey || event.metaKey || event.shiftKey || event.button !== 0) {
            return;
        }
        var root = trigger.closest('[data-video]');
        var facade = root && root.querySelector('[data-video-facade]');
        var src = trigger.getAttribute('data-video-src');
        if (!facade || !src) {
            return;
        }
        event.preventDefault();
        var iframe = document.createElement('iframe');
        iframe.className = 'video__iframe';
        iframe.src = src;
        iframe.title = trigger.getAttribute('data-video-title') || '';
        iframe.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
        iframe.allowFullscreen = true;
        iframe.referrerPolicy = 'strict-origin-when-cross-origin';
        facade.replaceWith(iframe);
        root.setAttribute('data-video-loaded', 'true');
        iframe.focus();
    });

    /* Video de fundo ----------------------------------------------------- */
    var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    var wide = window.matchMedia('(min-width: 768px)');
    var saveData = !!(navigator.connection && navigator.connection.saveData);

    document.querySelectorAll('[data-video-kind="background"]').forEach(function (root) {
        var video = root.querySelector('[data-bg-video]');
        var toggle = root.querySelector('[data-video-toggle]');
        var toggleLabel = root.querySelector('[data-video-toggle-label]');
        if (!video) {
            return;
        }
        var loaded = false;
        var onScreen = true;
        var userPaused = reduceMotion.matches;   // movimento reduzido: comeca pausado

        function allowed() {
            return wide.matches && !saveData;
        }

        function load() {
            if (loaded) {
                return;
            }
            video.querySelectorAll('source[data-src]').forEach(function (source) {
                source.src = source.getAttribute('data-src');
            });
            video.load();
            loaded = true;
        }

        function render() {
            var shouldPlay = allowed() && !userPaused && onScreen && !document.hidden;
            if (shouldPlay) {
                load();
                var promise = video.play();
                if (promise && promise.catch) {
                    promise.catch(function () { /* autoplay bloqueado: fica a capa */ });
                }
            } else if (!video.paused) {
                video.pause();
            }
            root.dataset.playing = String(shouldPlay);
            if (toggle) {
                toggle.hidden = !allowed();
                var playing = !userPaused;
                toggle.setAttribute('data-state', playing ? 'playing' : 'paused');
                if (toggleLabel) {
                    toggleLabel.textContent = playing ? root.dataset.labelPause : root.dataset.labelPlay;
                }
            }
        }

        video.addEventListener('playing', function () { root.classList.add('is-playing'); });

        if (toggle) {
            toggle.addEventListener('click', function () {
                userPaused = !userPaused;
                render();
            });
        }
        if ('IntersectionObserver' in window) {
            new IntersectionObserver(function (entries) {
                onScreen = entries[0].isIntersecting;
                render();
            }).observe(root);
        }
        document.addEventListener('visibilitychange', render);
        wide.addEventListener('change', render);
        reduceMotion.addEventListener('change', function () {
            if (reduceMotion.matches) {
                userPaused = true;
            }
            render();
        });
        render();
    });
})();
