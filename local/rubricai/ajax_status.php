<?php
/**
 * AJAX proxy for RAG status — called by the browser to poll ingestion progress.
 *
 * @package    local_rubricai
 */

define('AJAX_SCRIPT', true);
require_once(__DIR__ . '/../../config.php');
require_login();

$courseid = required_param('course_id', PARAM_INT);

header('Content-Type: application/json; charset=utf-8');

try {
    // We reuse the rag_client to call the Python /status/{course_id} endpoint.
    $status = \local_rubricai\rag_client::status($courseid);
    
    // Return only the inner data (which is the JSON from Python) 
    // to match the rubricai.js expectation.
    echo json_encode($status['data']);
} catch (\Exception $e) {

    echo json_encode(['status' => 'error', 'message' => $e->getMessage()]);
}
