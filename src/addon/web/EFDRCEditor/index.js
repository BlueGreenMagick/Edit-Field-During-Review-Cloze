/* Copyright: Ankitects Pty Ltd and contributors
 * License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html */
import { filterHTML } from "./htmlFilter";
export { wrap } from "./wrap";
export function pasteHTML(html, internal, extendedMode) {
    html = filterHTML(html, internal, extendedMode);
    if (html !== "") {
        setFormat("inserthtml", html);
    }
}
export function setFormat(cmd, arg) {
    // modified - removed nosave parameter and saveField call
    document.execCommand(cmd, false, arg);
}
