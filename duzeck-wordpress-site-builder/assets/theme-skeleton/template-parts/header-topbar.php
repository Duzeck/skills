<?php
/**
 * Barra superior do header (pre-header): contatos e redes do dado UNICO
 * da pagina de opcoes. $args: items (phone | whatsapp | email | hours | social | text).
 */
if (!defined('ABSPATH')) { exit; }

$items = (array) ($args['items'] ?? []);
if (!$items) {
    return;
}
$phone = project_option('company_phone');
$whatsapp = project_option('company_whatsapp');
$email = project_option('company_email');
?>
<div class="site-topbar" data-site-topbar>
    <div class="site-topbar__inner">
        <ul class="site-topbar__list" role="list">
            <?php foreach ($items as $item) : ?>
                <?php if ($item === 'phone' && project_phone_href($phone)) : ?>
                    <li class="site-topbar__item site-topbar__item--phone"><a href="<?php echo esc_attr(project_phone_href($phone)); ?>"><?php echo esc_html($phone); ?></a></li>
                <?php elseif ($item === 'whatsapp' && project_whatsapp_href($whatsapp)) : ?>
                    <li class="site-topbar__item site-topbar__item--whatsapp">
                        <a href="<?php echo esc_url(project_whatsapp_href($whatsapp, project_option('company_whatsapp_message'))); ?>" target="_blank" rel="noopener">
                            <span class="screen-reader-text"><?php esc_html_e('WhatsApp:', 'project-theme'); ?> </span><?php echo esc_html($whatsapp); ?>
                        </a>
                    </li>
                <?php elseif ($item === 'email' && project_email_href($email)) : ?>
                    <li class="site-topbar__item site-topbar__item--email"><a href="<?php echo esc_attr(project_email_href($email)); ?>"><?php echo esc_html($email); ?></a></li>
                <?php elseif ($item === 'hours' && project_option('company_hours')) : ?>
                    <li class="site-topbar__item site-topbar__item--hours"><?php echo esc_html(project_option('company_hours')); ?></li>
                <?php elseif ($item === 'text' && project_option('header_topbar_text')) : ?>
                    <li class="site-topbar__item site-topbar__item--text"><?php echo esc_html(project_option('header_topbar_text')); ?></li>
                <?php elseif ($item === 'social') : ?>
                    <li class="site-topbar__item site-topbar__item--social">
                        <?php get_template_part('template-parts/social-links', null, ['location' => 'header']); ?>
                    </li>
                <?php endif; ?>
            <?php endforeach; ?>
        </ul>
    </div>
</div>
