/* Copyright: Ankitects Pty Ltd and contributors
 * License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html */
import { filterHTML } from "./htmlFilter.js";
import { wrap } from "./wrap.js";
export function setFormat(cmd, arg, nosave = false) {
    // modified - removed saveField call
    document.execCommand(cmd, false, arg);
}
window.EFDRC.pasteHTML = function (html, internal, extendedMode) {
    html = filterHTML(html, internal, extendedMode);
    if (html !== "") {
        setFormat("inserthtml", html);
    }
};
window.EFDRC.wrap = wrap;
