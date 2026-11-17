/**
 * Abas e acordeoes (template-parts/tabs.php e accordion.php,
 * references/disclosures.md). Sem dependencias.
 *
 * Abas: padrao W3C APG "Tabs" com ativacao automatica - role tablist/tab/
 *   tabpanel, aria-selected, tabindex movel (so a aba ativa entra no Tab),
 *   setas esquerda/direita (circulam), Home/End. mobile=stack: abaixo de
 *   768px volta ao HTML sem JS (paineis empilhados com titulo).
 * Acordeao: o <details> ja faz tudo; aqui so o "um aberto por vez" para
 *   navegador sem suporte ao atributo name e o link direto.
 * Link direto (#id de item/painel), na carga e em hashchange: abre o item /
 *   seleciona a aba e rola ate ele (o scroll-padding do header vale).
 */
(function () {
    'use strict';

    var mobile = window.matchMedia('(max-width: 767px)');
    var tabsets = [];

    /* Abas ----------------------------------------------------------------- */
    function Tabs(root) {
        var list = root.querySelector('[data-tabs-list]');
        var tabs = Array.prototype.slice.call(root.querySelectorAll('[data-tabs-tab]'));
        var panels = Array.prototype.slice.call(root.querySelectorAll('[data-tabs-panel]'));
        if (!list || !tabs.length || tabs.length !== panels.length) {
            return null;
        }
        var stack = root.dataset.mobile === 'stack';
        var current = Math.min(tabs.length, Math.max(1, parseInt(root.dataset.active, 10) || 1)) - 1;
        var enabled = false;

        function select(index, focus) {
            current = (index + tabs.length) % tabs.length;
            tabs.forEach(function (tab, i) {
                var on = i === current;
                tab.setAttribute('aria-selected', String(on));
                tab.tabIndex = on ? 0 : -1;
                panels[i].hidden = !on;
            });
            root.dataset.selected = String(current + 1);
            if (focus) {
                tabs[current].focus();
            }
        }

        function enable() {
            list.hidden = false;
            list.setAttribute('role', 'tablist');
            tabs.forEach(function (tab, i) {
                tab.setAttribute('role', 'tab');
                panels[i].setAttribute('role', 'tabpanel');
                panels[i].setAttribute('aria-labelledby', tab.id);
                panels[i].tabIndex = 0;
            });
            root.classList.add('tabs--js');
            enabled = true;
            select(current, false);
        }

        function disable() {
            list.hidden = true;
            list.removeAttribute('role');
            tabs.forEach(function (tab, i) {
                ['role', 'aria-selected', 'tabindex'].forEach(function (attr) { tab.removeAttribute(attr); });
                ['role', 'aria-labelledby', 'tabindex'].forEach(function (attr) { panels[i].removeAttribute(attr); });
                panels[i].hidden = false;
            });
            root.classList.remove('tabs--js');
            root.dataset.selected = '';
            enabled = false;
        }

        function layout() {
            if (stack && mobile.matches) {
                if (enabled) { disable(); }
            } else if (!enabled) {
                enable();
            }
        }

        tabs.forEach(function (tab, i) {
            tab.addEventListener('click', function () { select(i, false); });
        });
        list.addEventListener('keydown', function (event) {
            var keys = { ArrowRight: current + 1, ArrowLeft: current - 1, Home: 0, End: tabs.length - 1 };
            if (event.key in keys) {
                event.preventDefault();
                select(keys[event.key], true);
            }
        });
        mobile.addEventListener('change', layout);
        layout();

        return {
            reveal: function (id) {
                for (var i = 0; i < panels.length; i++) {
                    if (panels[i].id === id || tabs[i].id === id) {
                        if (enabled) { select(i, false); }
                        return panels[i];
                    }
                }
                return null;
            }
        };
    }

    document.querySelectorAll('[data-tabs]').forEach(function (root) {
        var t = Tabs(root);
        if (t) { tabsets.push(t); }
    });

    /* Acordeao: "um aberto por vez" sem suporte nativo a details[name] ------ */
    if (!('name' in HTMLDetailsElement.prototype)) {
        document.querySelectorAll('[data-accordion][data-exclusive]').forEach(function (root) {
            root.addEventListener('toggle', function (event) {
                var opened = event.target;
                if (!opened.open) { return; }
                root.querySelectorAll('details[open]').forEach(function (other) {
                    if (other !== opened) { other.open = false; }
                });
            }, true);
        });
    }

    /* Link direto --------------------------------------------------------- */
    function reveal() {
        var id = decodeURIComponent(location.hash.slice(1));
        if (!id) { return; }
        var target = null;
        for (var i = 0; i < tabsets.length && !target; i++) {
            target = tabsets[i].reveal(id);
        }
        var el = target || document.getElementById(id);
        if (!el) { return; }
        var details = el.closest('details');
        if (details && !details.open) {
            details.open = true;
        }
        if (target || details) {
            el.scrollIntoView({ block: 'start' });
        }
    }
    reveal();
    window.addEventListener('hashchange', reveal);
})();
