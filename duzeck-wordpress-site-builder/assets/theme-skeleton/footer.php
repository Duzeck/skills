<?php
/**
 * Rodape (references/footer-social.md): colunas de inc/footer.php
 * (estrutura da referencia) + faixa inferior (copyright, CNPJ/razao
 * social, links legais, credito) + "voltar ao topo" (se a referencia mostra).
 * Todo texto vem do admin (Configuracoes do Site > Rodape/Empresa).
 */
if (!defined('ABSPATH')) { exit; }
$legal_name = project_option('company_legal_name');
$cnpj = project_option('company_cnpj');
$credit_text = project_option('footer_credit_text');
$credit_url = project_option('footer_credit_url');
?>
<footer class="site-footer" data-site-footer>
    <div class="site-footer__columns">
        <?php foreach (project_footer_columns() as $id => $col) : ?>
            <?php get_template_part('template-parts/footer-column', null, ['id' => $id, 'kind' => $col['kind'], 'social' => $col['social']]); ?>
        <?php endforeach; ?>
    </div>

    <div class="site-footer__bottom">
        <p class="site-footer__copy"><?php echo esc_html(project_footer_copyright()); ?></p>
        <?php if ($legal_name || $cnpj) : ?>
            <p class="site-footer__legal-id">
                <?php echo esc_html(trim($legal_name . ($legal_name && $cnpj ? ' · ' : '') . ($cnpj ? 'CNPJ ' . $cnpj : ''))); ?>
            </p>
        <?php endif; ?>
        <?php $legal = project_footer_legal_links(); ?>
        <?php if ($legal) : ?>
            <ul class="site-footer__legal" role="list">
                <?php foreach ($legal as [$label, $url]) : ?>
                    <li><a href="<?php echo esc_url($url); ?>"><?php echo esc_html($label); ?></a></li>
                <?php endforeach; ?>
            </ul>
        <?php endif; ?>
        <?php if ($credit_text) : ?>
            <p class="site-footer__credit">
                <?php if ($credit_url) : ?>
                    <a href="<?php echo esc_url($credit_url); ?>" target="_blank" rel="noopener"><?php echo esc_html($credit_text); ?><span class="screen-reader-text"> <?php esc_html_e('(abre em nova aba)', 'project-theme'); ?></span></a>
                <?php else : ?>
                    <?php echo esc_html($credit_text); ?>
                <?php endif; ?>
            </p>
        <?php endif; ?>
        <?php if (apply_filters('project_footer_back_to_top', false)) : ?>
            <a class="site-footer__top" href="#topo">
                <span class="site-footer__top-icon" aria-hidden="true"></span>
                <?php esc_html_e('Voltar ao topo', 'project-theme'); ?>
            </a>
        <?php endif; ?>
    </div>
</footer>

<?php wp_footer(); ?>
</body>
</html>
