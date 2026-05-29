<?php
/**
 * AJAX endpoint to return the full course activities and resources as JSON for Astro.
 *
 * @package    local_rubricai
 */

define('AJAX_SCRIPT', true);
require_once(__DIR__ . '/../../config.php');

// Enable CORS for frontend requests
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

$courseid = required_param('course_id', PARAM_INT);

header('Content-Type: application/json; charset=utf-8');

try {
    // Extract payload
    $payload = \local_rubricai\data_provider::get_course_full_evaluation_payload($courseid);
    echo json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
} catch (\Exception $e) {
    echo json_encode(['status' => 'error', 'message' => $e->getMessage()]);
}
