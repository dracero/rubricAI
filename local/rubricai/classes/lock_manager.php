<?php
namespace local_rubricai;

defined('MOODLE_INTERNAL') || die();

/**
 * Reusable lock/protection pattern for RubricAI steps.
 *
 * When a teacher has already advanced in the pedagogical workflow,
 * earlier steps become "locked" to prevent accidental data loss.
 * This class provides:
 * - is_locked($step): checks if the step has downstream content that would be lost
 * - render_lock_banner(): the yellow warning card + unlock button
 * - render_option(): renders a card/pill as either a clickable <a> or inert <span>
 */
class lock_manager {

    /**
     * Determine if arstep has downstream content that needs protection.
     *
     * Step 0: locked if d1, s_sugs, or instrument exist
     * Step 2: locked if d1 or s_sugs exist
     * Step 3: locked if s_sugs or instrument exist
     *
     * @param int $step The current step number
     * @return bool
     */
    public static function is_locked(int $step): bool {
        switch ($step) {
            case 0:
                return session_manager::has_any('d1', 's_sugs', 'instrument');
            case 1:
                return session_manager::has_any('d1', 'd2', 's_sugs', 'instrument');
            case 2:
                return session_manager::has_any('d1', 's_sugs');
            case 3:
                return session_manager::has_any('s_sugs', 'instrument');
            case 4:
                return session_manager::has_any('inst_content', 'rubric_content');
            default:
                return false;
        }
    }

    /**
     * Render the yellow lock banner with an unlock button.
     *
     * @param string     $title        Banner title (e.g. "🔒 Opción bloqueada")
     * @param string     $message      Description text
     * @param \moodle_url $unlock_url  URL for the unlock button
     * @param string     $btn_label    Button label (e.g. "🔓 Cambiar de modo")
     */
    public static function render_lock_banner(
        string $title,
        string $message,
        \moodle_url $unlock_url,
        string $btn_label
    ): void {
        echo \html_writer::start_tag('div', [
            'class' => 'rubricai-card',
            'style' => 'border-left: 5px solid #fac775; background: #fffcf0; margin-bottom:20px; padding:15px;',
        ]);
        echo \html_writer::tag('strong', $title, [
            'style' => 'color:#633806; display:block; margin-bottom:5px;',
        ]);
        echo \html_writer::tag('p', $message, [
            'style' => 'font-size:12px; margin-bottom:15px; color:#555;',
        ]);
        echo \html_writer::link($unlock_url, $btn_label, [
            'class' => 'rubricai-btn',
            'style' => 'border-color:#fac775; color:#633806;',
        ]);
        echo \html_writer::end_tag('div');
    }

    /**
     * Render an option element that respects the lock state.
     * If locked: renders an inert <span> with disabled styling.
     * If unlocked: renders a clickable <a>.
     *
     * @param string $content   Inner HTML content
     * @param string $url       Link URL (ignored when locked)
     * @param string $classes   CSS classes for the element
     * @param bool   $locked    Whether the option is locked
     * @param string $tag_type  The tag type for wrapping: 'a'/'span' determines open/close tag
     * @return array  ['open_tag', 'close_tag'] — caller echoes content between them
     */
    public static function option_tags(
        $url,
        string $classes,
        bool $locked
    ): array {
        if ($locked) {
            $open = \html_writer::start_tag('span', [
                'class' => $classes,
                'style' => 'opacity:0.6; cursor:not-allowed;',
            ]);
            $close = \html_writer::end_tag('span');
        } else {
            $open = \html_writer::start_tag('a', [
                'href'  => $url,
                'class' => $classes,
            ]);
            $close = \html_writer::end_tag('a');
        }
        return [$open, $close];
    }

    /**
     * Render a simple pill/option (used for dimension options in Step 3).
     * If locked: inert <span>. If unlocked: clickable <a>.
     *
     * @param string $label     Display label
     * @param string $url       Link URL
     * @param string $classes   CSS classes (e.g. "opt main")
     * @param bool   $locked    Whether the option is locked
     */
    public static function render_pill(
        string $label,
        $url,
        string $classes,
        bool $locked
    ): void {
        if ($locked) {
            echo \html_writer::tag('span', $label, [
                'class' => $classes,
                'style' => 'opacity:0.6; cursor:not-allowed;',
            ]);
        } else {
            echo \html_writer::link($url, $label, ['class' => $classes]);
        }
    }
}
