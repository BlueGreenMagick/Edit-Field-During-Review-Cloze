/* Copyright: Ankitects Pty Ltd and contributors
 * License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html */

import { filterHTML } from "./htmlFilter.js";
export { wrap } from "./wrap.js";


export function pasteHTML(
    html: string,
    internal: boolean,
    extendedMode: boolean
): void {
    html = filterHTML(html, internal, extendedMode);

    if (html !== "") {
        setFormat("inserthtml", html);
    }
}


export function setFormat(cmd: string, arg?: any, nosave: boolean = false): void {
    // modified - removed saveField call
    document.execCommand(cmd, false, arg);
}
