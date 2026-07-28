// Keyboard control — arrows move the viewpoint, Shift+arrows switch view
// presets, single letters toggle modes. Every binding is a thin call into the
// Viewer's public API, so the same actions are available to a GUI button.

export const KEYBOARD_DEFAULTS = {
    orbitStep: 15,    // degrees per arrow press
    panStep: 0.06,    // fraction of the visible height per press
    zoomStep: 1.15,   // multiplier per press
};

// Bound to the CONTAINER, not to window: an embedded viewer inside someone
// else's page must not swallow that page's arrow keys. Clicking the viewer
// focuses it; a host that wants keys to work immediately calls container.focus().
export function attachKeyboard(viewer, container, options = {}) {
    const opts = { ...KEYBOARD_DEFAULTS, ...options };

    const handlers = {
        ArrowLeft: (e) => (e.shiftKey ? viewer.stepView(-1) : orbit(e, -1, 0)),
        ArrowRight: (e) => (e.shiftKey ? viewer.stepView(1) : orbit(e, 1, 0)),
        ArrowUp: (e) => (e.shiftKey ? viewer.setView('top') : orbit(e, 0, 1)),
        ArrowDown: (e) => (e.shiftKey ? viewer.setView('bottom') : orbit(e, 0, -1)),
        '+': () => viewer.zoomBy(opts.zoomStep),
        '=': () => viewer.zoomBy(opts.zoomStep),
        '-': () => viewer.zoomBy(1 / opts.zoomStep),
        p: () => viewer.setProjection(viewer.projection === 'orthographic' ? 'perspective' : 'orthographic'),
        g: () => viewer.setGrid(!viewer.gridEnabled),
        r: () => viewer.resetView(),
    };

    // Ctrl turns the arrows into a pan: the point you look AT moves, instead of
    // you moving around it.
    function orbit(event, dx, dy) {
        if (event.ctrlKey) {
            viewer.panBy(-dx * opts.panStep, dy * opts.panStep);
        } else {
            viewer.orbitBy(dx * opts.orbitStep, dy * opts.orbitStep);
        }
    }

    const onKeyDown = (event) => {
        const handler = handlers[event.key] ?? handlers[event.key.toLowerCase()];
        if (!handler) return;
        event.preventDefault();   // arrows would otherwise scroll the host page
        handler(event);
    };
    const onPointerDown = () => container.focus();

    container.tabIndex = 0;
    container.style.outline = 'none';
    container.addEventListener('keydown', onKeyDown);
    container.addEventListener('pointerdown', onPointerDown);

    return () => {
        container.removeEventListener('keydown', onKeyDown);
        container.removeEventListener('pointerdown', onPointerDown);
    };
}
