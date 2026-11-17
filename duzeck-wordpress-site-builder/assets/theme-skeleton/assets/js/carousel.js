/**
 * Carrossel acessivel (template-parts/carousel.php, references/carousels.md).
 * Padrao W3C APG "Carousel", sem dependencias.
 *
 * A base e CSS scroll-snap: sem JS os slides continuam acessiveis
 * arrastando/rolando. Este arquivo acrescenta:
 *  - setas e bolinhas (uma por posicao de parada, nao por slide);
 *  - autoplay com botao de pausa (WCAG 2.2.2), que para ao passar o mouse,
 *    ao focar qualquer controle/slide, com a aba oculta ou fora da tela, e
 *    com prefers-reduced-motion comeca PAUSADO (o usuario pode dar play);
 *  - teclado (setas esquerda/direita no trilho), inert nos slides fora da
 *    tela (Tab nao entra em slide invisivel) e aria-live so sem autoplay.
 * Estado para o QA: data-index, data-playing.
 */
(function () {
    'use strict';

    var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

    function format(template, a, b) {
        return String(template || '').replace('%1$d', a).replace('%2$d', b).replace('%d', a);
    }

    function Carousel(root) {
        var track = root.querySelector('[data-carousel-track]');
        var slides = Array.prototype.slice.call(root.querySelectorAll('[data-carousel-slide]'));
        if (!track || slides.length < 2) {
            return;
        }

        var controls = root.querySelector('[data-carousel-controls]');
        var prev = root.querySelector('[data-carousel-prev]');
        var next = root.querySelector('[data-carousel-next]');
        var toggle = root.querySelector('[data-carousel-toggle]');
        var toggleLabel = root.querySelector('[data-carousel-toggle-label]');
        var dotsBox = root.querySelector('[data-carousel-dots]');
        var loop = root.dataset.loop === 'true';
        var hasAutoplay = root.dataset.autoplay === 'true';
        var interval = Math.max(3000, parseInt(root.dataset.interval, 10) || 6000);

        var index = 0;
        var dots = [];
        var timer = null;
        // Pausado pelo usuario (botao) - ou desde o inicio com movimento
        // reduzido; nos dois casos so o botao retoma.
        var userPaused = reduceMotion.matches;
        var hoverOrFocus = false;    // pausa temporaria
        var onScreen = true;

        function step() {
            return slides[1].offsetLeft - slides[0].offsetLeft || track.clientWidth;
        }

        function perView() {
            return Math.max(1, Math.round(track.clientWidth / step()));
        }

        function stops() {
            return Math.max(1, slides.length - perView() + 1);
        }

        function behavior() {
            return reduceMotion.matches ? 'auto' : 'smooth';
        }

        function goTo(target) {
            var last = stops() - 1;
            if (target > last) {
                target = loop || isPlaying() ? 0 : last;
            } else if (target < 0) {
                target = loop ? last : 0;
            }
            track.scrollTo({ left: slides[target].offsetLeft - slides[0].offsetLeft, behavior: behavior() });
            setIndex(target);
        }

        function setIndex(value) {
            index = Math.min(Math.max(0, value), stops() - 1);
            root.dataset.index = String(index);
            var visibleEnd = index + perView();
            slides.forEach(function (slide, i) {
                var hidden = i < index || i >= visibleEnd;
                slide.inert = hidden;
                slide.setAttribute('aria-hidden', hidden ? 'true' : 'false');
            });
            dots.forEach(function (dot, i) {
                if (i === index) {
                    dot.setAttribute('aria-current', 'true');
                } else {
                    dot.removeAttribute('aria-current');
                }
            });
            if (!loop) {
                if (prev) { prev.disabled = index === 0; }
                if (next) { next.disabled = index >= stops() - 1; }
            }
        }

        function syncFromScroll() {
            setIndex(Math.round(track.scrollLeft / step()));
        }

        function buildDots() {
            if (!dotsBox) {
                return;
            }
            var total = stops();
            if (dots.length === total) {
                return;
            }
            dotsBox.textContent = '';
            dots = [];
            for (var i = 0; i < total; i++) {
                var dot = document.createElement('button');
                dot.type = 'button';
                dot.className = 'carousel__dot';
                dot.setAttribute('data-carousel-dot', '');
                dot.setAttribute('aria-controls', track.id);
                dot.setAttribute('aria-label', format(root.dataset.labelDot, i + 1));
                dot.addEventListener('click', goTo.bind(null, i));
                dotsBox.appendChild(dot);
                dots.push(dot);
            }
            dotsBox.hidden = total < 2;
        }

        /* Autoplay ------------------------------------------------------- */
        function isPlaying() {
            return hasAutoplay && !userPaused;
        }

        function schedule() {
            clearTimeout(timer);
            var running = isPlaying() && !hoverOrFocus && onScreen && !document.hidden;
            root.dataset.playing = String(running);
            if (running) {
                timer = setTimeout(function () {
                    goTo(index + 1);
                    schedule();
                }, interval);
            }
        }

        function renderToggle() {
            var playing = isPlaying();
            track.setAttribute('aria-live', playing ? 'off' : 'polite');
            if (toggle) {
                var text = playing ? root.dataset.labelPause : root.dataset.labelPlay;
                if (toggleLabel) { toggleLabel.textContent = text; }
                toggle.setAttribute('data-state', playing ? 'playing' : 'paused');
            }
            schedule();
        }

        if (toggle) {
            toggle.addEventListener('click', function () {
                userPaused = !userPaused;
                renderToggle();
            });
        }

        root.addEventListener('mouseenter', function () { hoverOrFocus = true; schedule(); });
        root.addEventListener('mouseleave', function () {
            hoverOrFocus = root.contains(document.activeElement);
            schedule();
        });
        root.addEventListener('focusin', function () { hoverOrFocus = true; schedule(); });
        root.addEventListener('focusout', function (event) {
            if (!root.contains(event.relatedTarget)) {
                hoverOrFocus = root.matches(':hover');
                schedule();
            }
        });
        document.addEventListener('visibilitychange', schedule);
        if (reduceMotion.addEventListener) {
            reduceMotion.addEventListener('change', function () {
                if (reduceMotion.matches) {
                    userPaused = true;
                }
                renderToggle();
            });
        }
        if ('IntersectionObserver' in window) {
            new IntersectionObserver(function (entries) {
                onScreen = entries[0].isIntersecting;
                schedule();
            }, { threshold: 0.25 }).observe(root);
        }

        /* Navegacao manual ----------------------------------------------- */
        if (prev) { prev.addEventListener('click', function () { goTo(index - 1); }); }
        if (next) { next.addEventListener('click', function () { goTo(index + 1); }); }

        track.addEventListener('keydown', function (event) {
            if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
                event.preventDefault();
                goTo(index + (event.key === 'ArrowRight' ? 1 : -1));
            }
        });

        // Arrastar/rolar o trilho (touch, trackpad): sincroniza ao parar.
        if ('onscrollend' in window) {
            track.addEventListener('scrollend', syncFromScroll);
        } else {
            var scrollTimer = null;
            track.addEventListener('scroll', function () {
                clearTimeout(scrollTimer);
                scrollTimer = setTimeout(syncFromScroll, 120);
            }, { passive: true });
        }

        if ('ResizeObserver' in window) {
            new ResizeObserver(function () {
                buildDots();
                syncFromScroll();
            }).observe(track);
        }

        root.classList.add('carousel--js');
        if (controls) { controls.hidden = false; }
        buildDots();
        setIndex(0);
        renderToggle();
    }

    document.querySelectorAll('[data-carousel]').forEach(function (root) {
        Carousel(root);
    });
})();
