// Model schema validation.
//
// A MODEL is the content a consumer hands the viewer: axes, cells and views
// (see MODELS.md). Its shape is stated once, as data, in
// shared/model_schema.json — this module is only the interpreter of that
// statement, and preview3d/model.py is the same interpreter in Python. Stating
// the schema once is what makes "it validates" mean the same thing on both
// sides; a consumer's exporter checks against the same file the renderers read.
//
// Errors carry the PATH of the offending field — `axes[3].ends[1].names.canon`
// — because a model is generated data, and "invalid model" without a location
// is not something anyone can act on (Rule 1).

import SHARED from '../shared/spec.json';
import SCHEMA from '../shared/model_schema.json';
import { parseDirection } from './directions.js';

export const TYPES = SCHEMA.types;
export const ROOT_TYPE = SCHEMA.root;

const HEX = /^#[0-9a-fA-F]{6}$/;

function fail(where, message) {
    throw new Error(`${where}: ${message}`);
}

// A literal list, or a reference to one. '@dotted.path' reads shared/spec.json
// (the registers and tiers the whole component agrees on); '$field' reads the
// model's own declaration, which is how a model carrying only two registers is
// held to exactly those two.
function resolveList(reference, model, where) {
    if (Array.isArray(reference)) return reference;
    if (typeof reference !== 'string') {
        fail(where, `schema reference ${JSON.stringify(reference)} is neither a list nor a '@'/'$' path`);
    }
    if (reference === '*') return [];
    if (reference.startsWith('@')) {
        let node = SHARED;
        for (const part of reference.slice(1).split('.')) node = node[part];
        return [...node];
    }
    if (reference.startsWith('$')) return [...(model[reference.slice(1)] ?? [])];
    fail(where, `schema reference '${reference}' must start with '@' or '$'`);
    return [];
}

function checkValue(value, typeName, where, model) {
    if (TYPES[typeName]) {
        checkDeclared(value, TYPES[typeName], where, model);
        return;
    }
    switch (typeName) {
        case 'string':
            if (typeof value !== 'string' || !value) fail(where, `expected a non-empty string, got ${JSON.stringify(value)}`);
            break;
        case 'number':
            if (typeof value !== 'number' || !Number.isFinite(value)) fail(where, `expected a finite number, got ${JSON.stringify(value)}`);
            break;
        case 'boolean':
            if (typeof value !== 'boolean') fail(where, `expected true or false, got ${JSON.stringify(value)}`);
            break;
        case 'vector3':
            if (!Array.isArray(value) || value.length !== 3
                || !value.every((c) => typeof c === 'number' && Number.isFinite(c))) {
                fail(where, `expected 3 finite numbers, got ${JSON.stringify(value)}`);
            }
            break;
        case 'direction':
            try {
                parseDirection(value);
            } catch (error) {
                fail(where, error.message);
            }
            break;
        case 'color':
            if (typeof value !== 'string' || !HEX.test(value)) fail(where, `expected a '#rrggbb' colour, got ${JSON.stringify(value)}`);
            break;
        default:
            fail(where, `the schema names an unknown type '${typeName}'`);
    }
}

function checkDeclared(value, declared, where, model) {
    if (declared.map) {
        // A declared type may itself be a map (`names` is register -> seat); it
        // goes through the same body as a map FIELD so the two cannot diverge.
        checkMapBody(value, declared.map, where, model);
        return;
    }
    const fields = declared.fields;
    if (value === null || typeof value !== 'object' || Array.isArray(value)) {
        fail(where, `expected an object with fields ${Object.keys(fields).join(', ')}, got ${JSON.stringify(value)}`);
    }
    const unknown = Object.keys(value).filter((key) => !(key in fields) && !key.startsWith('_'));
    if (unknown.length) {
        fail(where, `unknown field(s) ${unknown.sort().join(', ')} — the schema allows ${Object.keys(fields).join(', ')}`);
    }
    for (const [name, field] of Object.entries(fields)) {
        if (!(name in value)) {
            if (field.required) fail(where, `missing required field '${name}'`);
            continue;
        }
        checkField(value[name], field, `${where}.${name}`, model);
    }
}

function checkField(value, field, where, model) {
    if (field.type === 'array') {
        if (!Array.isArray(value)) fail(where, `expected a list, got ${JSON.stringify(value)}`);
        if ('length' in field && value.length !== field.length) {
            fail(where, `expected exactly ${field.length} entries, got ${value.length}`);
        }
        const allowed = 'enum' in field ? resolveList(field.enum, model, where) : null;
        value.forEach((item, index) => {
            checkValue(item, field.of, `${where}[${index}]`, model);
            if (allowed && allowed.length && !allowed.includes(item)) {
                fail(`${where}[${index}]`, `${JSON.stringify(item)} is not one of ${allowed.join(', ')}`);
            }
        });
        return;
    }
    if (field.type === 'map') {
        checkMapBody(value, field, where, model);
        return;
    }
    if ('enum' in field) {
        const allowed = resolveList(field.enum, model, where);
        if (allowed.length && !allowed.includes(value)) {
            fail(where, `${JSON.stringify(value)} is not one of ${allowed.join(', ')}`);
        }
    }
    checkValue(value, field.type, where, model);
}

function checkMapBody(value, field, where, model) {
    if (value === null || typeof value !== 'object' || Array.isArray(value)) {
        fail(where, `expected an object, got ${JSON.stringify(value)}`);
    }
    const keys = field.keys ?? '*';
    if (keys !== '*') {
        const required = resolveList(keys, model, where);
        const missing = required.filter((key) => !(key in value));
        const extra = Object.keys(value).filter((key) => !required.includes(key));
        if (missing.length) fail(where, `missing entries for ${missing.join(', ')}`);
        if (extra.length) fail(where, `unexpected entries ${extra.sort().join(', ')} — allowed: ${required.join(', ')}`);
    }
    for (const [key, item] of Object.entries(value)) {
        checkValue(item, field.of, `${where}.${key}`, model);
    }
}

// Check `model` against the schema and return it unchanged, so a caller can
// write `model = validate(loaded)` and never hold an unchecked one.
export function validate(model) {
    checkValue(model, ROOT_TYPE, 'model', model);
    return model;
}
