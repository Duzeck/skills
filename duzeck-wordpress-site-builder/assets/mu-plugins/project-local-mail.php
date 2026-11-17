<?php
/**
 * Plugin Name: Local mail log (desenvolvimento)
 * Description: SO em ambiente local (WP_ENVIRONMENT_TYPE = local): intercepta wp_mail() e grava cada e-mail como JSON em wp-content/local-mail/ em vez de enviar. Fora do ambiente local nao faz nada.
 *
 * Copiado pelo scripts/scaffold_wp_project.py para wp-content/mu-plugins/.
 * Por que: o PHP do WAMP nao tem servidor de e-mail, entao wp_mail() falha
 * e o Contact Form 7 mostra "erro ao enviar" mesmo com o formulario certo.
 * Com o log, o QA prova que o envio aconteceu, para quem e com que conteudo
 * (scripts/capture_site.py --submit-forms --mail-log <pasta>), sem instalar
 * nada e sem mandar e-mail de verdade a partir da maquina local.
 *
 * Em producao: NAO e carregado (o ambiente nao e "local"); configure SMTP
 * autenticado (ex.: WP Mail SMTP) - ver references/forms.md.
 */

if (!defined('ABSPATH')) {
    exit;
}

if (!function_exists('wp_get_environment_type') || wp_get_environment_type() !== 'local') {
    return;
}

add_filter('pre_wp_mail', function ($return, $atts) {
    if ($return !== null) {
        return $return; // outro plugin ja tratou o envio
    }

    $dir = WP_CONTENT_DIR . '/local-mail';
    if (!is_dir($dir)) {
        wp_mkdir_p($dir);
        // A pasta fica dentro do site: bloqueia acesso pelo navegador.
        file_put_contents($dir . '/.htaccess', "Require all denied\n");
        file_put_contents($dir . '/index.php', "<?php\n// Silence is golden.\n");
    }

    $headers = $atts['headers'] ?? [];
    $entry = [
        'date' => gmdate('c'),
        'to' => array_values((array) ($atts['to'] ?? [])),
        'subject' => (string) ($atts['subject'] ?? ''),
        'message' => (string) ($atts['message'] ?? ''),
        'headers' => is_array($headers) ? array_values($headers) : preg_split('/\r\n|\r|\n/', (string) $headers, -1, PREG_SPLIT_NO_EMPTY),
        'attachments' => array_map('basename', (array) ($atts['attachments'] ?? [])),
    ];

    $file = sprintf('%s/%s-%s.json', $dir, gmdate('Ymd-His'), wp_generate_password(6, false));
    $written = file_put_contents(
        $file,
        wp_json_encode($entry, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)
    );

    // true = "enviado" para quem chamou wp_mail() (o CF7 mostra sucesso).
    return $written !== false;
}, 10, 2);
