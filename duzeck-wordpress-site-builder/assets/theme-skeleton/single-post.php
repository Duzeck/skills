<?php
/**
 * Post do blog (references/blog.md). CPTs usam single.php / single-<cpt>.php.
 * Imagem de destaque = LCP (eager + fetchpriority); data de publicacao e
 * de atualizacao em <time>; compartilhar por links (sem script de
 * terceiro); relacionados da mesma categoria; anterior/proximo.
 * JSON-LD BlogPosting: inc/blog.php.
 */
if (!defined('ABSPATH')) { exit; }
get_header();
$sidebar = defined('PROJECT_BLOG_SIDEBAR') && PROJECT_BLOG_SIDEBAR;
?>
<main id="conteudo" class="site-main site-main--post" tabindex="-1">
    <div class="blog-layout<?php echo $sidebar ? ' blog-layout--sidebar' : ''; ?>">
        <?php while (have_posts()) : the_post(); ?>
            <article <?php post_class('post-single blog-layout__main'); ?> data-post-single>
                <header class="post-single__header">
                    <?php echo project_post_category_link(); // escapado ?>
                    <h1 class="post-single__title"><?php the_title(); ?></h1>
                    <p class="post-single__meta">
                        <?php
                        /* translators: %s: data */
                        printf(esc_html__('Publicado em %s', 'project-theme'), project_post_time());
                        if (get_the_modified_date('Y-m-d') !== get_the_date('Y-m-d')) {
                            echo ' <span aria-hidden="true">·</span> ';
                            /* translators: %s: data */
                            printf(esc_html__('Atualizado em %s', 'project-theme'), project_post_time(null, true));
                        }
                        ?>
                        <?php if (get_the_author()) : ?>
                            <span aria-hidden="true">·</span> <?php echo esc_html(get_the_author()); ?>
                        <?php endif; ?>
                        <span aria-hidden="true">·</span> <?php echo esc_html(project_reading_time()); ?>
                    </p>
                </header>
                <?php if (has_post_thumbnail()) : ?>
                    <?php
                    project_media(get_post_thumbnail_id(), [
                        'ratio' => '16 / 9',
                        'alt' => (string) get_post_meta(get_post_thumbnail_id(), '_wp_attachment_image_alt', true),
                        'class' => 'post-single__image',
                        'size' => 'large',
                        'loading' => 'eager',
                    ]);
                    ?>
                <?php endif; ?>
                <div class="entry-content"><?php the_content(); ?></div>
                <?php the_tags('<p class="post-single__tags"><span class="screen-reader-text">' . esc_html__('Tags:', 'project-theme') . '</span> ', ', ', '</p>'); ?>

                <nav class="post-share" aria-label="<?php esc_attr_e('Compartilhar', 'project-theme'); ?>">
                    <p class="post-share__title" aria-hidden="true"><?php esc_html_e('Compartilhar', 'project-theme'); ?></p>
                    <ul role="list">
                        <?php foreach (project_share_links() as $key => [$label, $url]) : ?>
                            <li>
                                <a class="post-share__link post-share__link--<?php echo esc_attr($key); ?>" href="<?php echo esc_url($url); ?>"
                                    <?php echo $key === 'email' ? '' : 'target="_blank" rel="noopener"'; ?>>
                                    <span class="post-share__icon" aria-hidden="true"></span>
                                    <span class="screen-reader-text">
                                        <?php
                                        /* translators: %s: rede */
                                        printf(esc_html__('Compartilhar no %s', 'project-theme'), esc_html($label));
                                        echo $key === 'email' ? '' : ' ' . esc_html__('(abre em nova aba)', 'project-theme');
                                        ?>
                                    </span>
                                </a>
                            </li>
                        <?php endforeach; ?>
                    </ul>
                </nav>

                <?php
                the_post_navigation([
                    'aria_label' => __('Navegação entre posts', 'project-theme'),
                    'prev_text' => '<span class="post-nav__label">' . esc_html__('Anterior', 'project-theme') . '</span> %title',
                    'next_text' => '<span class="post-nav__label">' . esc_html__('Próximo', 'project-theme') . '</span> %title',
                ]);
                ?>
                <?php if (PROJECT_COMMENTS && (comments_open() || get_comments_number())) : ?>
                    <?php comments_template(); ?>
                <?php endif; ?>
            </article>
        <?php endwhile; ?>
        <?php if ($sidebar) : ?>
            <?php get_template_part('template-parts/blog-sidebar'); ?>
        <?php endif; ?>
    </div>

    <?php
    $cats = wp_get_post_categories(get_queried_object_id());
    $related = new WP_Query([
        'post_type' => 'post',
        'posts_per_page' => 3,
        'post__not_in' => [get_queried_object_id()],
        'category__in' => $cats,
        'ignore_sticky_posts' => true,
        'no_found_rows' => true,
    ]);
    ?>
    <?php if ($cats && $related->have_posts()) : ?>
        <section class="post-related" aria-labelledby="post-related-title" data-posts-related>
            <h2 id="post-related-title"><?php esc_html_e('Leia também', 'project-theme'); ?></h2>
            <ul class="post-grid" role="list">
                <?php while ($related->have_posts()) : $related->the_post(); ?>
                    <li><?php get_template_part('template-parts/post-card', null, ['heading_level' => 3, 'fields' => ['image', 'date', 'category']]); ?></li>
                <?php endwhile; wp_reset_postdata(); ?>
            </ul>
        </section>
    <?php endif; ?>
</main>
<?php get_footer(); ?>
