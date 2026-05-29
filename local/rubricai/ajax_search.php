<?php
/**
 * AJAX proxy for RAG search — called by the browser to query the Python service.
 *
 * @package    local_rubricai
 */

define('AJAX_SCRIPT', true);
require_once(__DIR__ . '/../../config.php');
require_login();

$courseid = required_param('course_id', PARAM_INT);
$query    = required_param('query', PARAM_RAW);

header('Content-Type: application/json; charset=utf-8');

if (empty($query)) {
    echo json_encode(['status' => 'error', 'message' => 'Query is empty']);
    die();
}

try {
    $result = \local_rubricai\rag_client::search($courseid, $query);
    echo json_encode($result);
} catch (\Exception $e) {
    echo json_encode(['status' => 'error', 'message' => $e->getMessage()]);
}
