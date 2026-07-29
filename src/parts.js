// Parts — addressing the individual elements of whatever is being shown, so a
// host can hide, dim or drop them one by one.
//
// A part is addressed by its PATH: the slash-joined chain of object names from
// the content root, e.g. `axes/arm:+x/label:1`. Naming is therefore the whole
// contract between a model and the host — see MODELS.md.

const PATH_SEPARATOR = '/';

// Anything the renderer actually draws.
function isDrawable(object) {
    return Boolean(object.isMesh || object.isSprite || object.isLine || object.isPoints);
}

function partName(object, index) {
    return object.name || `${object.type}#${index}`;
}

// Depth-first walk yielding [object, path] for every named node under root.
function* walk(root, prefix = '') {
    for (let i = 0; i < root.children.length; i++) {
        const child = root.children[i];
        const path = prefix + partName(child, i);
        yield [child, path];
        yield* walk(child, path + PATH_SEPARATOR);
    }
}

// Flat list of the content's parts, in tree order. `depth` lets a UI indent
// the list without re-parsing paths; `drawable` marks the nodes that carry
// geometry (a pure group is a switch for its subtree, nothing more).
export function collectParts(root) {
    const parts = [];
    for (const [object, path] of walk(root)) {
        parts.push({
            path,
            name: object.name || object.type,
            type: object.type,
            depth: path.split(PATH_SEPARATOR).length - 1,
            drawable: isDrawable(object),
            visible: object.visible,
            opacity: partOpacity(object),
            color: partColor(object),
        });
    }
    return parts;
}

export function findPart(root, path) {
    for (const [object, candidate] of walk(root)) {
        if (candidate === path) return object;
    }
    return null;
}

// Resolve or fail loudly — a typo in a path must never look like "nothing to do".
function requirePart(root, path) {
    const object = findPart(root, path);
    if (!object) {
        const known = collectParts(root).map((p) => p.path).join(', ');
        throw new Error(`Unknown part '${path}' — available: ${known || '(none)'}`);
    }
    return object;
}

// Hiding a group hides its whole subtree, which is exactly what a switch group
// in a model is for (one of N labels visible at a time).
export function setPartVisible(root, path, visible) {
    requirePart(root, path).visible = visible;
}

// Show exactly one child of a group and hide its siblings — the "3 legend
// terms, one shown at a time" case, in a single call.
export function showOnly(root, groupPath, childName) {
    const group = requirePart(root, groupPath);
    let found = false;
    for (let i = 0; i < group.children.length; i++) {
        const child = group.children[i];
        const matches = partName(child, i) === childName;
        child.visible = matches;
        found = found || matches;
    }
    if (!found) {
        const names = group.children.map((c, i) => partName(c, i)).join(', ');
        throw new Error(`Group '${groupPath}' has no child '${childName}' — available: ${names || '(none)'}`);
    }
}

// A part's opacity is its OWN, and it multiplies down its subtree — dimming a
// group dims everything under it without touching what those children say about
// themselves. That is the LIGHT renderer's model too (a node's opacity times its
// ancestors'), and the two must agree or `list_parts` reports two different
// numbers for the same part.
//
// Pushing the value straight onto every descendant's material instead — which is
// what this did — makes a child claim its parent's dimming as its own, and makes
// re-lighting one child silently escape the group's dimming.
export function setPartOpacity(root, path, alpha) {
    requirePart(root, path).userData.preview3dOpacity = alpha;
    applyEffectiveOpacity(root, 1);
}

function applyEffectiveOpacity(object, inherited) {
    const effective = inherited * (object.userData?.preview3dOpacity ?? 1);
    if (isDrawable(object)) applyOpacity(object, effective);
    for (const child of object.children) applyEffectiveOpacity(child, effective);
}

// Detach and release a part for good. Hiding is what you want for toggling;
// this is for content that must not survive in memory.
export function removePart(root, path) {
    const object = requirePart(root, path);
    object.traverse((node) => {
        node.geometry?.dispose();
        for (const material of materialsOf(node)) material.dispose();
    });
    object.removeFromParent();
}

// ---- Internals -------------------------------------------------------------

function materialsOf(object) {
    if (!object.material) return [];
    return Array.isArray(object.material) ? object.material : [object.material];
}

// What was SET on this part, not what its material ended up at — the material
// also carries whatever its ancestors contributed, and reporting that would make
// a child of a dimmed group look as though someone had dimmed the child.
function partOpacity(object) {
    return object.userData?.preview3dOpacity ?? 1;
}

// What colour a part actually wears, as '#RRGGBB', or null for a pure group.
// Reported because a host needs it for a legend and because it is the ONLY way
// a test can check that a computed palette (axiscolors.js) came out the same in
// both renderers — the picture cannot be compared, but the value can.
function partColor(object) {
    if (object.userData?.preview3dColor) return object.userData.preview3dColor.toUpperCase();
    for (const material of materialsOf(object)) {
        if (material.color) return `#${material.color.getHexString().toUpperCase()}`;
    }
    return null;
}

function applyOpacity(object, alpha) {
    const materials = materialsOf(object).map((material) => {
        // A material is routinely SHARED — between an arm's shaft and its tip
        // here, across whole meshes in a real glTF. Dimming one part must not
        // dim its neighbours, so the first change gives the object its own copy.
        const owned = material.userData.preview3dOwned
            ? material
            : Object.assign(material.clone(), { userData: { preview3dOwned: true } });
        owned.opacity = alpha;
        owned.transparent = alpha < 1 || material.transparent;
        // Without this a translucent shell writes depth and hides whatever sits
        // inside it — the opposite of why anyone makes a part translucent.
        owned.depthWrite = alpha >= 1;
        return owned;
    });
    object.material = Array.isArray(object.material) ? materials : materials[0];
}
