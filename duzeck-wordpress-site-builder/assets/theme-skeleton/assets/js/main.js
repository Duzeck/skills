/**
 * JS do projeto.
 *
 * O bloco de navegacao abaixo faz parte do esqueleto (references/navigation.md)
 * e so age se o header tiver os data-attributes de header.php. Sem
 * dependencias e SEM listener de "scroll": tudo com ResizeObserver e
 * IntersectionObserver (nao roda a cada pixel rolado, nao trava a rolagem).
 *
 *   1. --header-height: altura real do header sticky, usada no
 *      scroll-padding-top (ancora nunca para escondida atras do header).
 *   2. .is-scrolled no header quando a pagina sai do topo.
 *   3. Scroll-spy (single page): aria-current="location" no item do menu
 *      da secao que esta na tela.
 *   4. Menu mobile: aria-expanded, Esc, clique fora, fecha ao escolher item
 *      (abre o PAINEL inteiro: menu(s), acoes e botao de destaque).
 *   5. Submenus (references/header-menu.md): padrao W3C "disclosure" - um
 *      botao com aria-expanded ao lado de cada item com filhos; abre no
 *      clique/Enter/seta para baixo, fecha com Esc (foco volta ao botao),
 *      ao sair com Tab e no clique fora; hover so como conveniencia no
 *      desktop com mouse. Sem JS: :hover e :focus-within (CSS).
 *   6. Busca do header (<details>): Esc e clique fora fecham; foco no campo.
 *
 * Sem JS o site continua funcionando: header sticky e ancoras sao CSS puro
 * e o menu mobile fica aberto. Adicione abaixo do bloco so o que o layout
 * realmente precisar (ex.: filtro AJAX, se decidido no Blueprint).
 */
/* Formularios (CF7): envio com erro leva o foco ao primeiro campo invalido
   - o CF7 marca aria-invalid e a mensagem, mas deixa o foco no botao; quem
   usa teclado/leitor de tela precisa cair direto no que corrigir. */
document.addEventListener('wpcf7invalid', function (event) {
    var form = event.target;
    // O evento chega ANTES de o CF7 marcar aria-invalid nos campos: espera
    // ele terminar e usa a lista de campos invalidos do proprio evento.
    setTimeout(function () {
        var detail = event.detail && event.detail.apiResponse;
        var fields = (detail && detail.invalid_fields) || [];
        var first = null;
        if (fields.length && fields[0].field) {
            first = form.querySelector('[name="' + fields[0].field + '"], [name="' + fields[0].field + '[]"]');
        }
        first = first || form.querySelector('[aria-invalid="true"]');
        if (first) {
            first.focus();
        }
    }, 0);
});

(function () {
    'use strict';

    var header = document.querySelector('[data-site-header]');
    if (!header) {
        return;
    }

    var root = document.documentElement;
    var navs = Array.prototype.slice.call(header.querySelectorAll('[data-nav]'));
    var nav = navs[0] || null;
    var panel = header.querySelector('[data-nav-panel]') || nav;
    var toggle = header.querySelector('[data-nav-toggle]');
    var isSticky = header.hasAttribute('data-sticky');
    var isTransparent = header.hasAttribute('data-transparent');
    var headerHeight = header.offsetHeight;
    var onHeaderResize = [];

    function navIsOpen() {
        return !!panel && panel.classList.contains('is-open');
    }

    /* 1. Altura do header -> --header-height ---------------------------- */
    // Tambem no header transparente: a margem negativa que o poe sobre o
    // hero usa a altura real.
    if (isSticky || isTransparent) {
        var applyHeight = function (height) {
            headerHeight = Math.ceil(height);
            root.style.setProperty('--header-height', headerHeight + 'px');
            onHeaderResize.forEach(function (fn) { fn(); });
        };
        applyHeight(header.offsetHeight);

        if ('ResizeObserver' in window) {
            new ResizeObserver(function (entries) {
                // Menu mobile aberto aumenta o header: nao conta como altura
                // do header (evita o ciclo altura -> max-height -> altura).
                if (navIsOpen()) {
                    return;
                }
                var box = entries[0].borderBoxSize && entries[0].borderBoxSize[0];
                var height = box ? box.blockSize : header.offsetHeight;
                if (Math.abs(height - headerHeight) >= 1) {
                    applyHeight(height);
                }
            }).observe(header);
        }

        // Entrada direta com #ancora: o navegador rolou antes de saber a
        // altura real do header - reposiciona uma vez, sem animacao.
        if (location.hash.length > 1) {
            var initialTarget = document.getElementById(decodeURIComponent(location.hash.slice(1)));
            if (initialTarget) {
                requestAnimationFrame(function () {
                    initialTarget.scrollIntoView({ block: 'start', behavior: 'instant' });
                });
            }
        }
    }

    /* 2. Estado rolado ---------------------------------------------------- */
    if (isSticky && 'IntersectionObserver' in window) {
        var sentinel = document.createElement('div');
        sentinel.setAttribute('aria-hidden', 'true');
        sentinel.style.cssText = 'position:absolute;top:0;left:0;width:1px;height:1px;pointer-events:none;';
        document.body.prepend(sentinel);
        new IntersectionObserver(function (entries) {
            header.classList.toggle('is-scrolled', !entries[0].isIntersecting);
        }).observe(sentinel);
    }

    /* 3. Scroll-spy (single page) ----------------------------------------- */
    if (nav && header.hasAttribute('data-scrollspy') && 'IntersectionObserver' in window) {
        var here = location.origin + location.pathname;
        var spyItems = [];
        header.querySelectorAll('[data-nav] a[href*="#"]').forEach(function (link) {
            var url = new URL(link.href, location.href);
            if (url.hash.length < 2 || url.origin + url.pathname !== here) {
                return;
            }
            var section = document.getElementById(decodeURIComponent(url.hash.slice(1)));
            if (section) {
                spyItems.push({ link: link, section: section });
            }
        });

        if (spyItems.length) {
            var visible = new Set();
            var setCurrent = function (item) {
                spyItems.forEach(function (it) {
                    if (it === item) {
                        it.link.setAttribute('aria-current', 'location');
                    } else {
                        it.link.removeAttribute('aria-current');
                    }
                });
            };
            var pickCurrent = function () {
                // A primeira secao (ordem do documento) dentro da faixa logo
                // abaixo do header; nenhuma na faixa = mantem a ultima marcada.
                for (var i = 0; i < spyItems.length; i++) {
                    if (visible.has(spyItems[i].section)) {
                        setCurrent(spyItems[i]);
                        return;
                    }
                }
            };

            var spy = null;
            var buildSpy = function () {
                if (spy) {
                    spy.disconnect();
                }
                visible.clear();
                spy = new IntersectionObserver(function (entries) {
                    entries.forEach(function (entry) {
                        if (entry.isIntersecting) {
                            visible.add(entry.target);
                        } else {
                            visible.delete(entry.target);
                        }
                    });
                    pickCurrent();
                }, { rootMargin: '-' + (headerHeight + 1) + 'px 0px -60% 0px' });
                spyItems.forEach(function (it) { spy.observe(it.section); });
            };
            buildSpy();

            var rebuildPending = false;
            onHeaderResize.push(function () {
                if (rebuildPending) {
                    return;
                }
                rebuildPending = true;
                requestAnimationFrame(function () {
                    rebuildPending = false;
                    buildSpy();
                });
            });

            // Fim da pagina: a ultima secao costuma ser curta (contato) e nunca
            // chega a faixa - quando o rodape aparece, ela vira a atual.
            var pageEnd = document.querySelector('.site-footer') || spyItems[spyItems.length - 1].section;
            new IntersectionObserver(function (entries) {
                if (entries[0].isIntersecting && root.scrollTop > 0) {
                    setCurrent(spyItems[spyItems.length - 1]);
                }
            }, { threshold: 0.5 }).observe(pageEnd);
        }
    }

    /* 4. Menu mobile ------------------------------------------------------ */
    if (panel && toggle) {
        header.classList.add('site-header--js');
        toggle.hidden = false;

        var setOpen = function (open) {
            toggle.setAttribute('aria-expanded', String(open));
            panel.classList.toggle('is-open', open);
            header.classList.toggle('is-nav-open', open);
        };

        toggle.addEventListener('click', function () {
            setOpen(!navIsOpen());
        });

        // Escolher um item (ancora ou pagina) fecha o menu.
        panel.addEventListener('click', function (event) {
            if (event.target.closest('a')) {
                setOpen(false);
            }
        });

        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && navIsOpen()) {
                setOpen(false);
                toggle.focus();
            }
        });

        document.addEventListener('click', function (event) {
            if (navIsOpen() && !header.contains(event.target)) {
                setOpen(false);
            }
        });

        // Voltou para o layout desktop com o menu aberto: fecha.
        var desktop = window.matchMedia('(min-width: 768px)');
        desktop.addEventListener('change', function (event) {
            if (event.matches) {
                setOpen(false);
            }
        });
    }

    /* 5. Submenus ---------------------------------------------------------- */
    var subItems = [];
    var hoverable = window.matchMedia('(hover: hover) and (min-width: 768px)');
    var closeSubmenus = function (except) {
        subItems.forEach(function (it) {
            if (it.li !== except) { it.set(false); }
        });
    };
    header.querySelectorAll('[data-nav] .menu-item-has-children').forEach(function (li, i) {
        var link = li.querySelector(':scope > a');
        var sub = li.querySelector(':scope > .sub-menu');
        if (!link || !sub) {
            return;
        }
        sub.id = sub.id || 'submenu-' + (i + 1);
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'submenu-toggle';
        btn.setAttribute('aria-expanded', 'false');
        btn.setAttribute('aria-controls', sub.id);
        btn.innerHTML = '<span class="submenu-toggle__icon" aria-hidden="true"></span><span class="screen-reader-text"></span>';
        btn.querySelector('.screen-reader-text').textContent =
            (header.dataset.labelSubmenu || 'Submenu de %s').replace('%s', link.textContent.trim());
        link.after(btn);

        var set = function (open, returnFocus) {
            btn.setAttribute('aria-expanded', String(open));
            li.classList.toggle('is-submenu-open', open);
            if (!open && returnFocus) { btn.focus(); }
        };
        subItems.push({ li: li, set: set });

        btn.addEventListener('click', function () {
            var open = btn.getAttribute('aria-expanded') !== 'true';
            closeSubmenus(li);
            set(open);
        });
        li.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && li.classList.contains('is-submenu-open')) {
                event.stopPropagation();          // nao fecha o menu mobile junto
                set(false, true);
            } else if (event.key === 'ArrowDown' && document.activeElement === btn) {
                event.preventDefault();
                closeSubmenus(li);
                set(true);
                var first = sub.querySelector('a');
                if (first) { first.focus(); }
            }
        });
        li.addEventListener('focusout', function (event) {
            if (!li.contains(event.relatedTarget)) { set(false); }
        });
        li.addEventListener('mouseenter', function () {
            if (hoverable.matches) { closeSubmenus(li); set(true); }
        });
        li.addEventListener('mouseleave', function () {
            if (hoverable.matches) { set(false); }
        });
    });
    if (subItems.length) {
        header.classList.add('has-submenu-js');
        document.addEventListener('click', function (event) {
            if (!header.contains(event.target)) { closeSubmenus(null); }
        });
    }

    /* 6. Busca do header --------------------------------------------------- */
    var search = header.querySelector('[data-header-search]');
    if (search) {
        search.addEventListener('toggle', function () {
            if (search.open) {
                var input = search.querySelector('input[type="search"], input[name="s"]');
                if (input) { input.focus(); }
            }
        });
        search.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && search.open) {
                event.stopPropagation();
                search.open = false;
                search.querySelector('summary').focus();
            }
        });
        document.addEventListener('click', function (event) {
            if (search.open && !search.contains(event.target)) { search.open = false; }
        });
    }
})();
