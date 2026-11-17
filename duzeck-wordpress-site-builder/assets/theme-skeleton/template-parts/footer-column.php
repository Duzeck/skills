<?php
/**
 * Uma coluna do rodape (inc/footer.php). $args: id, kind, social (icones
 * das redes ao fim da coluna).
 * Cada coluna e uma <section> nomeada pelo titulo (h2) quando houver.
 */
if (!defined('ABSPATH')) { exit; }

$id = (string) ($args['id'] ?? '');
$kind = (string) ($args['kind'] ?? 'custom');
$title = project_footer_column_title($id);
$title_id = 'footer-col-' . sanitize_title($id);
?>
<section class="footer-col footer-col--<?php echo esc_attr($kind); ?>" data-footer-col="<?php echo esc_attr($id); ?>"
    <?php echo $title ? 'aria-labelledby="' . esc_attr($title_id) . '"' : ''; ?>>
    <?php if ($title) : ?>
        <h2 class="footer-col__title" id="<?php echo esc_attr($title_id); ?>"><?php echo esc_html($title); ?></h2>
    <?php endif; ?>

    <?php if ($kind === 'about') : ?>
        <?php $logo = project_image_id(project_option('footer_logo') ?: project_option('company_logo')); ?>
        <?php if ($logo) : ?>
            <a class="footer-col__logo" href="<?php echo esc_url(home_url('/')); ?>">
                <?php echo wp_get_attachment_image($logo, 'medium', false, ['alt' => get_bloginfo('name'), 'loading' => 'lazy']); ?>
            </a>
        <?php endif; ?>
        <?php if (project_option('footer_about_text')) : ?>
            <p class="footer-col__text"><?php echo project_lines(project_option('footer_about_text')); ?></p>
        <?php endif; ?>

    <?php elseif ($kind === 'menu') : ?>
        <nav aria-label="<?php echo esc_attr($title ?: __('Links do rodapé', 'project-theme')); ?>">
            <?php wp_nav_menu(['theme_location' => 'footer_' . $id, 'container' => false, 'fallback_cb' => false, 'depth' => 1]); ?>
        </nav>

    <?php elseif ($kind === 'contact') : ?>
        <?php
        $address = project_option('company_address');
        $phone = project_option('company_phone');
        $whatsapp = project_option('company_whatsapp');
        $email = project_option('company_email');
        $hours = project_option('company_hours');
        ?>
        <address class="footer-contact">
            <ul role="list">
                <?php if ($address) : ?>
                    <li class="footer-contact__item footer-contact__item--address">
                        <a href="<?php echo esc_url(project_address_href($address)); ?>" target="_blank" rel="noopener"><?php echo project_lines($address); ?><span class="screen-reader-text"> <?php esc_html_e('(abre o mapa em nova aba)', 'project-theme'); ?></span></a>
                    </li>
                <?php endif; ?>
                <?php if ($phone && project_phone_href($phone)) : ?>
                    <li class="footer-contact__item footer-contact__item--phone">
                        <a href="<?php echo esc_attr(project_phone_href($phone)); ?>"><?php echo esc_html($phone); ?></a>
                    </li>
                <?php endif; ?>
                <?php /* Mesmo numero do telefone (caso comum): uma linha so, como as referencias mostram. */ ?>
                <?php if ($whatsapp && project_whatsapp_href($whatsapp) && project_phone_digits($whatsapp) !== project_phone_digits($phone)) : ?>
                    <li class="footer-contact__item footer-contact__item--whatsapp">
                        <a href="<?php echo esc_url(project_whatsapp_href($whatsapp, project_option('company_whatsapp_message'))); ?>" target="_blank" rel="noopener">
                            <span class="screen-reader-text"><?php esc_html_e('WhatsApp:', 'project-theme'); ?> </span><?php echo esc_html($whatsapp); ?>
                        </a>
                    </li>
                <?php endif; ?>
                <?php if ($email && project_email_href($email)) : ?>
                    <li class="footer-contact__item footer-contact__item--email">
                        <a href="<?php echo esc_attr(project_email_href($email)); ?>"><?php echo esc_html($email); ?></a>
                    </li>
                <?php endif; ?>
                <?php if ($hours) : ?>
                    <li class="footer-contact__item footer-contact__item--hours"><?php echo project_lines($hours); ?></li>
                <?php endif; ?>
            </ul>
        </address>

    <?php elseif ($kind === 'social') : ?>
        <?php get_template_part('template-parts/social-links', null, ['location' => 'footer', 'label' => $title ?: __('Redes sociais', 'project-theme')]); ?>

    <?php elseif ($kind === 'newsletter') : ?>
        <?php if (project_option('footer_newsletter_text')) : ?>
            <p class="footer-col__text"><?php echo project_lines(project_option('footer_newsletter_text')); ?></p>
        <?php endif; ?>
        <?php project_form('footer_newsletter_form'); ?>

    <?php elseif ($kind === 'hours') : ?>
        <p class="footer-col__text"><?php echo project_lines(project_option('company_hours')); ?></p>

    <?php else : ?>
        <div class="footer-col__text"><?php echo wp_kses_post(wpautop((string) project_option('footer_' . $id . '_text'))); ?></div>
    <?php endif; ?>

    <?php if (!empty($args['social']) && $kind !== 'social') : ?>
        <?php get_template_part('template-parts/social-links', null, ['location' => 'footer']); ?>
    <?php endif; ?>
</section>
