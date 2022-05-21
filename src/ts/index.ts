/* Copyright: Ankitects Pty Ltd and contributors
 * License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html */

import { filterHTML } from "./html-filter/index";
import { wrapInternal } from "./wrap";

export function setFormat(
  cmd: string,
  arg?: any,
  nosave: boolean = false
): void {
  // modified - removed saveField call
  document.execCommand(cmd, false, arg);
}

declare global {
  interface Window {
    EFDRC: any;
  }
}

window.EFDRC.pasteHTML = function (
  html: string,
  internal: boolean,
  extendedMode: boolean
): void {
  html = filterHTML(html, internal, extendedMode);

  if (html !== "") {
    setFormat("inserthtml", html);
  }
};

window.EFDRC.wrapInternal = wrapInternal;
