(function (exports) {
    'use strict';

    // Copyright: Ankitects Pty Ltd and contributors
    // License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
    function isHTMLElement(elem) {
        return elem instanceof HTMLElement;
    }
    function isNightMode() {
        return document.body.classList.contains("nightMode");
    }

    // Copyright: Ankitects Pty Ltd and contributors
    // License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
    function removeNode(element) {
        var _a;
        (_a = element.parentNode) === null || _a === void 0 ? void 0 : _a.removeChild(element);
    }
    function iterateElement(filter, fragment) {
        for (const child of [...fragment.childNodes]) {
            filter(child);
        }
    }
    const filterNode = (elementFilter) => (node) => {
        switch (node.nodeType) {
            case Node.COMMENT_NODE:
                removeNode(node);
                break;
            case Node.DOCUMENT_FRAGMENT_NODE:
                iterateElement(filterNode(elementFilter), node);
                break;
            case Node.ELEMENT_NODE:
                iterateElement(filterNode(elementFilter), node);
                elementFilter(node);
                break;
            // do nothing
        }
    };

    // Copyright: Ankitects Pty Ltd and contributors
    // License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
    const stylingNightMode = {
        "font-weight": [],
        "font-style": [],
        "text-decoration-line": [],
    };
    const stylingLightMode = {
        color: [],
        "background-color": ["transparent"],
        ...stylingNightMode,
    };
    const stylingInternal = [
        "background-color",
        "font-size",
        "font-family",
        "width",
        "height",
        "max-width",
        "max-height",
    ];
    const allowPropertiesBlockValues = (allowBlock) => (property, value) => Object.prototype.hasOwnProperty.call(allowBlock, property) &&
        !allowBlock[property].includes(value);
    const blockProperties = (block) => (property) => !block.includes(property);
    const filterStyling = (predicate) => (element) => {
        for (const property of [...element.style]) {
            const value = element.style.getPropertyValue(property);
            if (!predicate(property, value)) {
                element.style.removeProperty(property);
            }
        }
    };
    const filterStylingNightMode = filterStyling(allowPropertiesBlockValues(stylingNightMode));
    const filterStylingLightMode = filterStyling(allowPropertiesBlockValues(stylingLightMode));
    const filterStylingInternal = filterStyling(blockProperties(stylingInternal));

    // Copyright: Ankitects Pty Ltd and contributors
    function filterAttributes(attributePredicate, element) {
        for (const attr of [...element.attributes]) {
            const attrName = attr.name.toUpperCase();
            if (!attributePredicate(attrName)) {
                element.removeAttributeNode(attr);
            }
        }
    }
    function allowNone(element) {
        filterAttributes(() => false, element);
    }
    const allow = (attrs) => (element) => filterAttributes((attributeName) => attrs.includes(attributeName), element);
    function unwrapElement(element) {
        element.replaceWith(...element.childNodes);
    }
    function filterSpan(element) {
        const filterAttrs = allow(["STYLE"]);
        filterAttrs(element);
        const filterStyle = isNightMode() ? filterStylingNightMode : filterStylingLightMode;
        filterStyle(element);
    }
    const tagsAllowedBasic = {
        BR: allowNone,
        IMG: allow(["SRC", "ALT"]),
        DIV: allowNone,
        P: allowNone,
        SUB: allowNone,
        SUP: allowNone,
        TITLE: removeNode,
    };
    const tagsAllowedExtended = {
        ...tagsAllowedBasic,
        A: allow(["HREF"]),
        B: allowNone,
        BLOCKQUOTE: allowNone,
        CODE: allowNone,
        DD: allowNone,
        DL: allowNone,
        DT: allowNone,
        EM: allowNone,
        FONT: allow(["COLOR"]),
        H1: allowNone,
        H2: allowNone,
        H3: allowNone,
        I: allowNone,
        LI: allowNone,
        OL: allowNone,
        PRE: allowNone,
        RP: allowNone,
        RT: allowNone,
        RUBY: allowNone,
        SPAN: filterSpan,
        STRONG: allowNone,
        TABLE: allowNone,
        TD: allow(["COLSPAN", "ROWSPAN"]),
        TH: allow(["COLSPAN", "ROWSPAN"]),
        TR: allow(["ROWSPAN"]),
        U: allowNone,
        UL: allowNone,
    };
    const filterElementTagsAllowed = (tagsAllowed) => (element) => {
        const tagName = element.tagName;
        if (Object.prototype.hasOwnProperty.call(tagsAllowed, tagName)) {
            tagsAllowed[tagName](element);
        }
        else if (element.innerHTML) {
            unwrapElement(element);
        }
        else {
            removeNode(element);
        }
    };
    const filterElementBasic = filterElementTagsAllowed(tagsAllowedBasic);
    const filterElementExtended = filterElementTagsAllowed(tagsAllowedExtended);
    function filterElementInternal(element) {
        if (isHTMLElement(element)) {
            filterStylingInternal(element);
        }
    }

    // Copyright: Ankitects Pty Ltd and contributors
    var FilterMode;
    (function (FilterMode) {
        FilterMode[FilterMode["Basic"] = 0] = "Basic";
        FilterMode[FilterMode["Extended"] = 1] = "Extended";
        FilterMode[FilterMode["Internal"] = 2] = "Internal";
    })(FilterMode || (FilterMode = {}));
    const filters = {
        [FilterMode.Basic]: filterElementBasic,
        [FilterMode.Extended]: filterElementExtended,
        [FilterMode.Internal]: filterElementInternal,
    };
    const whitespace = /[\n\t ]+/g;
    function collapseWhitespace(value) {
        return value.replace(whitespace, " ");
    }
    function trim(value) {
        return value.trim();
    }
    const outputHTMLProcessors = {
        [FilterMode.Basic]: (outputHTML) => trim(collapseWhitespace(outputHTML)),
        [FilterMode.Extended]: trim,
        [FilterMode.Internal]: trim,
    };
    function filterHTML(html, internal, extended) {
        const template = document.createElement("template");
        template.innerHTML = html;
        const mode = getFilterMode(internal, extended);
        const content = template.content;
        const filter = filterNode(filters[mode]);
        filter(content);
        return outputHTMLProcessors[mode](template.innerHTML);
    }
    function getFilterMode(internal, extended) {
        if (internal) {
            return FilterMode.Internal;
        }
        else if (extended) {
            return FilterMode.Extended;
        }
        else {
            return FilterMode.Basic;
        }
    }

    // Copyright: Ankitects Pty Ltd and contributors
    // License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
    /**
     * Gecko has no .getSelection on ShadowRoot, only .activeElement
     */
    function getSelection(element) {
        const root = element.getRootNode();
        if (root.getSelection) {
            return root.getSelection();
        }
        return document.getSelection();
    }
    /**
     * Browser has potential support for multiple ranges per selection built in,
     * but in reality only Gecko supports it.
     * If there are multiple ranges, the latest range is the _main_ one.
     */
    function getRange(selection) {
        const rangeCount = selection.rangeCount;
        return rangeCount === 0 ? null : selection.getRangeAt(rangeCount - 1);
    }

    // Copyright: Ankitects Pty Ltd and contributors
    function wrappedExceptForWhitespace(text, front, back) {
        const match = text.match(/^(\s*)([^]*?)(\s*)$/);
        return match[1] + front + match[2] + back + match[3];
    }
    function moveCursorInside(selection, postfix) {
        const range = getRange(selection);
        range.setEnd(range.endContainer, range.endOffset - postfix.length);
        range.collapse(false);
        selection.removeAllRanges();
        selection.addRange(range);
    }
    function wrapInternal(base, front, back, plainText) {
        const selection = getSelection(base);
        const range = getRange(selection);
        if (!range) {
            return;
        }
        const wasCollapsed = range.collapsed;
        const content = range.cloneContents();
        const span = document.createElement("span");
        span.appendChild(content);
        if (plainText) {
            const new_ = wrappedExceptForWhitespace(span.innerText, front, back);
            document.execCommand("inserttext", false, new_);
        }
        else {
            const new_ = wrappedExceptForWhitespace(span.innerHTML, front, back);
            document.execCommand("inserthtml", false, new_);
        }
        if (wasCollapsed &&
            /* ugly solution: treat <anki-mathjax> differently than other wraps */ !front.includes("<anki-mathjax")) {
            moveCursorInside(selection, back);
        }
    }

    /* Copyright: Ankitects Pty Ltd and contributors
     * License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html */
    function setFormat(cmd, arg, nosave = false) {
        // modified - removed saveField call
        document.execCommand(cmd, false, arg);
    }
    window.EFDRC.pasteHTML = function (html, internal, extendedMode) {
        html = filterHTML(html, internal, extendedMode);
        if (html !== "") {
            setFormat("inserthtml", html);
        }
    };
    window.EFDRC.wrapInternal = wrapInternal;

    exports.setFormat = setFormat;

    Object.defineProperty(exports, '__esModule', { value: true });

    return exports;

})({});
//# sourceMappingURL=editor.js.map
