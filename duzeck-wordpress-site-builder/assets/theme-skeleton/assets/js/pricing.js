/**
 * Seletor de periodo dos planos (template-parts/pricing.php,
 * references/tables-pricing.md). Sem JS os precos de todos os periodos
 * aparecem; aqui: mostra o seletor (botoes com aria-pressed), deixa so o
 * periodo escolhido e anuncia a troca para leitor de tela (aria-live).
 */
(function () {
    'use strict';

    document.querySelectorAll('[data-pricing]').forEach(function (root) {
        var toggle = root.querySelector('[data-pricing-toggle]');
        var status = root.querySelector('[data-pricing-status]');
        if (!toggle) {
            return;
        }
        var options = Array.prototype.slice.call(toggle.querySelectorAll('[data-billing-option]'));

        function select(key, announce) {
            root.dataset.billing = key;
            options.forEach(function (option) {
                option.setAttribute('aria-pressed', String(option.dataset.billingOption === key));
            });
            root.querySelectorAll('[data-price-for]').forEach(function (price) {
                price.hidden = price.dataset.priceFor !== key;
            });
            if (announce && status) {
                var label = options.filter(function (o) { return o.dataset.billingOption === key; })[0];
                status.textContent = (toggle.getAttribute('aria-label') || '') + ': ' + (label ? label.textContent.trim() : key);
            }
        }

        options.forEach(function (option) {
            option.addEventListener('click', function () { select(option.dataset.billingOption, true); });
        });
        toggle.hidden = false;
        root.classList.add('pricing--js');
        select(root.dataset.billing || options[0].dataset.billingOption, false);
    });
})();
