<?php
/**
 * Barra de aviso no topo (references/hero-banners.md): "Frete gratis esta
 * semana" - texto e link do admin (announcement_text / _link_label /
 * _link_target). Fechavel: a escolha fica no navegador da pessoa
 * (localStorage), atrelada ao TEXTO - aviso novo volta a aparecer.
 * O script inline logo abaixo esconde a barra ANTES da pintura se ja foi
 * fechada (sem piscar nem salto de layout). Sem JS: aparece, sem fechar.
 */
if (!defined('ABSPATH')) { exit; }

$text = trim((string) project_option('announcement_text'));
if ($text === '') {
    return;
}
$label = trim((string) project_option('announcement_link_label'));
$target = project_option('announcement_link_target');
$key = 'aviso-' . substr(md5($text), 0, 10);
?>
<div class="announcement" data-announcement="<?php echo esc_attr($key); ?>" role="region" aria-label="<?php esc_attr_e('Aviso', 'project-theme'); ?>">
    <p class="announcement__text">
        <?php echo esc_html($text); ?>
        <?php if ($label && $target && $target !== '#') : ?>
            <a href="<?php echo esc_url(project_target_url($target)); ?>"><?php echo esc_html($label); ?></a>
        <?php endif; ?>
    </p>
    <button type="button" class="announcement__close" data-announcement-close hidden>
        <span class="announcement__close-icon" aria-hidden="true"></span>
        <span class="screen-reader-text"><?php esc_html_e('Fechar aviso', 'project-theme'); ?></span>
    </button>
</div>
<script>
(function () {
    var bar = document.currentScript.previousElementSibling;
    try {
        if (localStorage.getItem(bar.dataset.announcement) === '1') { bar.hidden = true; return; }
    } catch (e) { return; }   // sem localStorage: aviso fica, sem botao de fechar
    var btn = bar.querySelector('[data-announcement-close]');
    btn.hidden = false;
    btn.addEventListener('click', function () {
        try { localStorage.setItem(bar.dataset.announcement, '1'); } catch (e) {}
        bar.hidden = true;
        // O foco nao se perde com o botao removido: vai para o logo (o skip
        // link apareceria de repente na tela).
        var next = document.querySelector('.site-logo');
        if (next) { next.focus(); }
    });
})();
</script>
