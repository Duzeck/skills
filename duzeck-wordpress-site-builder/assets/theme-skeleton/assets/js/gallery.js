/**
 * Lightbox da galeria (template-parts/gallery.php, references/galleries.md).
 * <dialog> nativo com showModal(): o navegador ja prende o foco, torna o
 * resto da pagina inerte e fecha com Esc. Este arquivo acrescenta
 * navegacao (setas do teclado, botoes, gesto de arrastar), contador
 * "3 de 12" (aria-live), legenda, foco devolvido a miniatura ao fechar e
 * pre-carregamento so da proxima foto. Sem JS, cada miniatura e um link
 * para a foto grande.
 */
(function () {
    'use strict';

    var dialog = null;
    var parts = {};
    var items = [];
    var index = 0;
    var root = null;
    var trigger = null;

    function format(template, a, b) {
        return String(template || '').replace('%1$d', a).replace('%2$d', b);
    }

    function button(cls, labelKey) {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'lightbox__' + cls;
        b.innerHTML = '<span class="lightbox__icon" aria-hidden="true"></span><span class="screen-reader-text"></span>';
        b.dataset.labelKey = labelKey;
        return b;
    }

    function build() {
        dialog = document.createElement('dialog');
        dialog.className = 'lightbox';
        parts.close = button('close', 'labelClose');
        parts.prev = button('prev', 'labelPrev');
        parts.next = button('next', 'labelNext');
        parts.figure = document.createElement('figure');
        parts.figure.className = 'lightbox__figure';
        parts.img = document.createElement('img');
        parts.img.className = 'lightbox__img';
        parts.img.decoding = 'async';
        parts.caption = document.createElement('figcaption');
        parts.caption.className = 'lightbox__caption';
        parts.counter = document.createElement('p');
        parts.counter.className = 'lightbox__counter';
        parts.counter.setAttribute('aria-live', 'polite');
        parts.figure.append(parts.img, parts.caption);
        // Fechar primeiro: e onde o foco cai ao abrir.
        dialog.append(parts.close, parts.figure, parts.counter, parts.prev, parts.next);
        document.body.appendChild(dialog);

        parts.close.addEventListener('click', function () { dialog.close(); });
        parts.prev.addEventListener('click', function () { show(index - 1); });
        parts.next.addEventListener('click', function () { show(index + 1); });
        dialog.addEventListener('keydown', function (event) {
            if (event.key === 'ArrowLeft') { event.preventDefault(); show(index - 1); }
            if (event.key === 'ArrowRight') { event.preventDefault(); show(index + 1); }
        });
        // Clique no fundo escuro (fora do conteudo) fecha.
        dialog.addEventListener('click', function (event) {
            if (event.target === dialog) { dialog.close(); }
        });
        dialog.addEventListener('close', function () {
            parts.img.removeAttribute('src');
            if (trigger) { trigger.focus(); }
        });
        // Arrastar para o lado (touch/caneta/mouse).
        var startX = null;
        parts.figure.addEventListener('pointerdown', function (event) { startX = event.clientX; });
        parts.figure.addEventListener('pointerup', function (event) {
            if (startX === null) { return; }
            var dx = event.clientX - startX;
            startX = null;
            if (Math.abs(dx) > 50) { show(index + (dx < 0 ? 1 : -1)); }
        });
    }

    function labels() {
        [parts.close, parts.prev, parts.next].forEach(function (b) {
            b.querySelector('.screen-reader-text').textContent = root.dataset[b.dataset.labelKey] || '';
        });
        dialog.setAttribute('aria-label', root.dataset.label || '');
    }

    function show(i) {
        index = (i + items.length) % items.length;
        var item = items[index];
        parts.img.src = item.href;
        parts.img.alt = item.dataset.alt || '';
        parts.caption.textContent = item.dataset.caption || '';
        parts.caption.hidden = !item.dataset.caption;
        parts.counter.textContent = format(root.dataset.labelCounter, index + 1, items.length);
        var single = items.length < 2;
        parts.prev.hidden = single;
        parts.next.hidden = single;
        dialog.dataset.index = String(index);
        if (!single) {
            new Image().src = items[(index + 1) % items.length].href; // so a proxima
        }
    }

    document.addEventListener('click', function (event) {
        var link = event.target.closest('[data-gallery-item]');
        if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.button !== 0) {
            return;
        }
        var gallery = link.closest('[data-gallery][data-lightbox="true"]');
        if (!gallery || typeof HTMLDialogElement === 'undefined') {
            return; // sem <dialog>: segue o link para a foto
        }
        event.preventDefault();
        if (!dialog) { build(); }
        root = gallery;
        trigger = link;
        items = Array.prototype.slice.call(gallery.querySelectorAll('[data-gallery-item]'));
        labels();
        show(items.indexOf(link));
        dialog.showModal();
    });
})();
