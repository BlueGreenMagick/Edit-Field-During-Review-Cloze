/* Copyright: Ankitects Pty Ltd and contributors
 * License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html */
import { setFormat } from "./index.js";
function wrappedExceptForWhitespace(text, front, back) {
    const match = text.match(/^(\s*)([^]*?)(\s*)$/);
    return match[1] + front + match[2] + back + match[3];
}
function moveCursorPastPostfix(selection, postfix) {
    const range = selection.getRangeAt(0);
    range.setStart(range.startContainer, range.startOffset - postfix.length);
    range.collapse(true);
    selection.removeAllRanges();
    selection.addRange(range);
}
function wrapInternal(front, back, plainText) {
    // modified - assign window.getSelection() to selection
    const selection = window.getSelection();
    const range = selection.getRangeAt(0);
    const content = range.cloneContents();
    const span = document.createElement("span");
    span.appendChild(content);
    if (plainText) {
        const new_ = wrappedExceptForWhitespace(span.innerText, front, back);
        setFormat("inserttext", new_);
    }
    else {
        const new_ = wrappedExceptForWhitespace(span.innerHTML, front, back);
        setFormat("inserthtml", new_);
    }
    if (!span.innerHTML) {
        moveCursorPastPostfix(selection, back);
    }
}
export function wrap(front, back) {
    wrapInternal(front, back, false);
}
