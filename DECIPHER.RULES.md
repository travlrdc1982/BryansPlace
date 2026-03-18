# DECIPHER.RULES.md

## Decipher XML Programming Rules for the PRISM Survey

> A comprehensive catalogue of errors encountered and corrections applied across **5 Claude Code sessions** and **4 branches** during the development of the PRISM survey in Decipher (compat="146"). Rules are derived from commit history AND cross-referenced against the [official Forsta XML Style System](https://support.focusvision.com/) and Survey Tag documentation. These rules should be followed whenever generating or editing Decipher survey XML.

### Sessions Covered

| Session | Branch | Commits | Scope |
|---------|--------|---------|-------|
| `0187UwxU4oF75c2DY3tdjwtF` | `master` | 31 | Initial XML build, CSS/JS inclusion, CDATA crashes, bracket substitution |
| `01777fUxzyQFtds1r2gx4QNv` | `claude/fix-pnta-checkbox-XcTcj` | 9 | PNTA coding, navigation, termination logic |
| `01Cg4ZeHQ6p8ALaivgTN9Hqh` | `claude/maxdiff-xml-implementation-kt2v0` | 57 | MaxDiff infrastructure, design files, quotas, element IDs, form submission |
| `01T58f6ksM59wyStB6ApP9yv` | `claude/survey-new-media-section-cks59` | 55 | NM section, checkbox/rating sync, `ans{id}` naming, Less compile, themevars, INF refactor |

---

## Table of Contents

1. [XML Structure & Parsing](#1-xml-structure--parsing)
2. [Namespaces & Attributes](#2-namespaces--attributes)
3. [Character Encoding](#3-character-encoding)
4. [Square Brackets & Variable Substitution](#4-square-brackets--variable-substitution)
5. [CDATA Blocks & Tag-Name Collisions](#5-cdata-blocks--tag-name-collisions)
6. [CSS Inclusion (respview.client.css)](#6-css-inclusion-respviewclientcss)
7. [JavaScript Inclusion (respview.client.js)](#7-javascript-inclusion-respviewclientjs)
8. [Question Elements & Validation](#8-question-elements--validation)
9. [Survey Flow & Page Breaks](#9-survey-flow--page-breaks)
10. [Screening & Termination Logic](#10-screening--termination-logic)
11. [Native Input Interop — Radios](#11-native-input-interop--radios)
12. [Native Input Interop — Checkboxes](#12-native-input-interop--checkboxes)
13. [Native Input Interop — Ratings & Selects](#13-native-input-interop--ratings--selects)
14. [Decipher Input Naming Convention (ans{id})](#14-decipher-input-naming-convention-ansid)
15. [Form Submission & Navigation](#15-form-submission--navigation)
16. [Samplesources & Exit Pages](#16-samplesources--exit-pages)
17. [Theme References & Themevars](#17-theme-references--themevars)
18. [CSS Content Restrictions](#18-css-content-restrictions)
19. [DOM Element IDs](#19-dom-element-ids)
20. [Exec Blocks & Python Logic](#20-exec-blocks--python-logic)
21. [Comments](#21-comments)
22. [Quota Management](#22-quota-management)
23. [Design File Loading](#23-design-file-loading)
24. [HTML Element Restrictions](#24-html-element-restrictions)
25. [Style Block Naming](#25-style-block-naming)
26. [Conditional Row Visibility](#26-conditional-row-visibility)
27. [Official Forsta Reference Notes](#27-official-forsta-reference-notes)

---

## 1. XML Structure & Parsing

### Rule 1.1: One `<?xml?>` declaration only
**Error:** Duplicate `<?xml version="1.0"?>` declaration embedded inside the `<survey>` body caused a fatal WKDFJ save error.
**Fix:** Ensure only a single `<?xml?>` declaration exists at line 1 of the file.
**Session:** 1 | **Commit:** `a77c375`

### Rule 1.2: Quote all attribute values
**Error:** Unquoted `style` attributes in `onerror` handlers caused XML parser failures.
**Fix:** Every attribute value must be enclosed in double quotes: `style="display:none"`, not `style=display:none`.
**Session:** 1 | **Commit:** `a77c375`

### Rule 1.3: Wrap `<exec>` blocks with CDATA when they contain `<` operators
**Error:** Python comparison operators like `col < len(groups)` inside `<exec>` blocks caused XML parse errors because `<` is an XML special character.
**Fix:** Wrap exec content in CDATA:
```xml
<exec><![CDATA[
if col < len(groups):
    val = groups[col]
]]></exec>
```
**Session:** 4 | **Commit:** `9fde39e`

### Rule 1.4: Use `<note>` instead of HTML comments
**Error:** `<!-- -->` style comments are not supported in Decipher's Survey Editor and cause XML parse errors.
**Fix:** Use `<note>` elements:
```xml
<note>This is a comment</note>
```
**Sessions:** 3, 4 | **Commits:** `09ac5f2`, `1addf75`

---

## 2. Namespaces & Attributes

### Rule 2.1: Do NOT declare `xmlns:builder`
**Error:** Declaring `xmlns:builder` in the `<survey>` tag caused a "redefined" validation error. Decipher provides this namespace automatically.
**Fix:** Omit `xmlns:builder`. Only declare `xmlns:html` and `xmlns:ss`.
**Session:** 1 | **Commit:** `1f77c24`

### Rule 2.2: Do NOT use `builder:wizardCompleted`
**Error:** Depends on the `xmlns:builder` namespace which cannot be redeclared.
**Fix:** Remove `builder:wizardCompleted` from the survey element.
**Session:** 1 | **Commit:** `1f77c24`

### Rule 2.3: Namespace declarations may block saving on some instances
**Error:** On the maxdiff branch, `xmlns:html` and `xmlns:ss` declarations prevented the survey from saving.
**Fix:** If saving fails with namespace errors, try removing the declarations — some Decipher instances auto-provide them.
**Session:** 3 | **Commit:** `9d3c54f`

### Rule 2.4: Valid namespace prefixes for compat="146"
Safe to use (when the instance supports them):
- `xmlns:html="http://www.w3.org/1999/xhtml"` — for `html:showNumber` etc.
- `xmlns:ss="http://www.decipherinc.com/ss"` — for `ss:disableBackButton`, `ss:enableNavigation`, `ss:hideProgressBar`

---

## 3. Character Encoding

### Rule 3.1: No raw non-ASCII characters in CDATA blocks
**Error:** 4-byte UTF-8 emoji (U+1F418, U+1FACF) and special dashes (U+2011, U+2014) caused fatal server errors (XSVJV/DBNZJ).
**Fix:** Replace ALL non-ASCII characters with HTML numeric entities:
- `&#x1F418;` instead of raw emoji
- `&#x2014;` instead of em-dash
- `&#x2019;` instead of right single quote
- `&#x2026;` instead of ellipsis
**Sessions:** 1, 4 | **Commits:** `5979b51`, `a77c375`, `969f0b5`

### Rule 3.2: Exec blocks must be ASCII-only
**Error:** Em dashes and other non-ASCII characters in `<exec>` and `<note>` elements caused Decipher compilation errors.
**Fix:** Use only ASCII characters inside `<exec>` blocks. Replace em dashes with `--`, smart quotes with straight quotes.
**Session:** 3 | **Commit:** `082b133`

### Rule 3.3: Use numeric entities, not named entities in CDATA
**Error:** `&rsquo;` and `&mdash;` named entities caused XML parsing issues.
**Fix:** Use numeric entities: `&#x2019;` instead of `&rsquo;`, `&#x2014;` instead of `&mdash;`.
**Session:** 4 | **Commit:** `969f0b5`

---

## 4. Square Brackets & Variable Substitution

### Rule 4.1: NEVER use square brackets in `<html>` CDATA content
**Error:** Decipher's `<html>` element runs `replaceVariables()` on its CDATA content, interpreting `[...]` as variable pipe references. This caused crashes in multiple sessions:
- `pattern="[0-9]*"` → "Variable 0-9 not set"
- `input[type="submit"]` → variable substitution crash
- `c[0]` in JS → variable substitution crash
- `[four / five]` in text → KeyError
- `[type=submit]` in inline onclick → KeyError
**Fix:** Move CSS/JS to `<style name="respview.client.css">` / `respview.client.js` blocks where brackets are safe. For text, spell out bracketed content. For JS, use `.item(0)` instead of `[0]`.
**Sessions:** 1, 2, 3 | **Commits:** `00bd236`, `9d15559`, `33796eb`, `78646b9`, `d8ae9ed`, `656752a`, `6919491`, `87466f2`, `f9ca19d`

### Rule 4.2: Avoid `pattern` attributes with bracket syntax
**Error:** `pattern="[0-9]*"` on question elements triggers variable substitution.
**Fix:** Use `type="tel"` and `inputmode="numeric"` instead.
**Session:** 1 | **Commit:** `00bd236`

### Rule 4.3: Replace bracket CSS selectors if inside `<html>` elements
**Error:** `input[type="submit"]` CSS selector triggered variable substitution.
**Fix:** Use class selectors (`.button`, `.nextPage`) instead. Or move CSS to `respview.client.css`.
**Sessions:** 1, 3 | **Commits:** `9d15559`, `656752a`

### Rule 4.4: No bracket notation in JS inside `<html>` CDATA
**Error:** `c[0]` array access in JavaScript was caught by Decipher's variable parser.
**Fix:** Use `.item(0)` for HTMLCollection access. Or better: move all JS to `respview.client.js`.
**Session:** 3 | **Commit:** `87466f2`

### Rule 4.5: Literal bracket text in titles/subtitles is interpolated
**Error:** Text like `[four / five]` in question titles caused KeyError.
**Fix:** Remove brackets from display text: "four or five" instead of "[four / five]".
**Session:** 2 | **Commit:** `78646b9`

---

## 5. CDATA Blocks & Tag-Name Collisions

### Rule 5.1: `</style>` inside CDATA prematurely closes outer `<style>` elements
**Error:** Decipher performs text-level matching of `</style>`. Inner CSS `</style>` tags inside CDATA prematurely terminated the outer element.
**Fix:** Use `<html label="...">` for inline content containing `</style>`. Or use dedicated `respview.client.css` blocks.
**Sessions:** 1, 4 | **Commits:** `1eaef3c`, `a86a0a2`

### Rule 5.2: Do NOT put inline `<style>` tags inside `<style mode="before">` CDATA
**Error:** An inline `<style>` tag inside a `<style mode="before">` CDATA block caused a fatal error — `</style>` was interpreted as closing the outer element.
**Fix:** Move CSS to the global `respview.client.css` block.
**Session:** 4 | **Commit:** `a86a0a2`

---

## 6. CSS Inclusion (respview.client.css)

### Rule 6.1: Use `<style name="respview.client.css">` for all global CSS
**Correct structure:**
```xml
<style name="respview.client.css" mode="after"><![CDATA[
<link href="https://fonts.googleapis.com/..." rel="stylesheet">
<style>
/* your CSS here — brackets are safe */
</style>
]]></style>
```
The CDATA content is injected **raw** into the HTML `<head>`. You MUST include the inner `<style>...</style>` tags — Decipher does NOT auto-wrap.
**Session:** 1 | **Commit:** `52ee305`

### Rule 6.2: Do NOT use `<style type="text/css">` inside CDATA
**Error:** The `type` attribute was treated as invalid CSS text, preventing all styles from loading.
**Fix:** Use a plain `<style>` tag — no `type` attribute.
**Session:** 1 | **Commit:** `6fa015b`

### Rule 6.3: `mode="after"` loads CSS after Decipher's defaults
Use `mode="after"` to ensure your custom CSS overrides Decipher defaults.

### Rule 6.4: Scope page-specific CSS with `with=` attribute
Per-question or per-page CSS can use the `with` attribute to scope:
```xml
<style name="respview.client.css" mode="after" with="QMD1,QMD3"><![CDATA[
<style>/* MaxDiff-specific CSS */</style>
]]></style>
```
Ensure `with=` values match actual question labels in the survey.
**Session:** 4 | **Commit:** `89ab8c8`

---

## 7. JavaScript Inclusion (respview.client.js)

### Rule 7.1: Use `<style name="respview.client.js" wrap="ready">` for page-scoped JS
```xml
<style name="respview.client.js" wrap="ready"><![CDATA[
// runs inside jQuery(document).ready()
]]></style>
```
`wrap="ready"` auto-wraps in `<script>` + jQuery ready. Do NOT manually add `<script>` tags or jQuery wrappers.
**Per official Forsta docs:** Use the `with` argument to restrict JS to specific pages (comma-delimited question labels):
```xml
<style name="respview.client.js" wrap="ready" with="Q1,Q2"><![CDATA[
// only runs on pages containing Q1 or Q2
]]></style>
```
**Session:** 1 | **Commit:** `52ee305` | **Source:** Official Forsta "Including JavaScript in a Survey" docs

### Rule 7.2: For globally-scoped helper functions, omit `wrap="ready"`
**Error:** Shared helper functions placed in `wrap="ready"` were scoped inside the jQuery ready closure and invisible to per-question scripts.
**Fix:** Use `mode="after"` without `wrap="ready"` for functions that must be globally callable:
```xml
<style name="respview.client.js" mode="after"><![CDATA[
<script>
function nmSyncRating(q, row, val) { /* ... */ }
</script>
]]></style>
```
**Session:** 4 | **Commit:** `8c79241`

### Rule 7.3: Do NOT put `<script>` tags inside `<html>` CDATA
**Error:** Inline scripts don't execute reliably and are subject to variable substitution (Rule 4.1).
**Fix:** Move all JavaScript to `respview.client.js` style blocks.
**Session:** 1 | **Commit:** `b46ebc2`

### Rule 7.4: Use jQuery, not vanilla JS
Decipher bundles jQuery. Standard pattern: `jQuery(document).ready()`. Prefer jQuery selectors for DOM manipulation.

### Rule 7.5: `survey.footer` and `survey.respview` are NOT valid style names
**Error:** Attempted to use `<style name="survey.footer">` and `<style name="survey.respview">` for shared JS — neither is supported.
**Fix:** Use `<style name="respview.client.js" mode="after">` for global JS.
**Session:** 4 | **Commits:** `a22061b`, `63fdc4f`, `8c79241`

---

## 8. Question Elements & Validation

### Rule 8.1: `where="execute"` IS valid on `<radio>` and `<checkbox>` — but may fail on `<text>`
**CORRECTION:** The original rule stated `where="execute"` is "only valid on `<html>` elements." **Per official Forsta docs**, `where="execute"` is the standard pattern for hidden computed questions:
```xml
<radio label="vAge" where="execute">
  <title>Age Group (Hidden Question)</title>
  <row label="r1">18-24</row>
</radio>
<checkbox label="vOver18" atleast="0" where="execute">
  <title>Over 18? (Hidden Question)</title>
  <row label="yes">Yes</row>
</checkbox>
```
The error in Session 1 (`XSVJV` on `<text>` with `where="execute"`) may have been specific to `<text>` elements or may have had a different root cause. Both `cond="0"` and `where="execute"` work for hiding questions:
- `where="execute"`: Decipher processes the question server-side only (official pattern for computed variables)
- `cond="0"`: Question is never shown but IS declared (alternative approach)
**Session:** 1 | **Commits:** `1653e66`, `535df34` | **Corrected by:** Official Forsta Exec Tag docs

### Rule 8.2: Every variable referenced in `<exec>` must be declared
**Error:** `<exec>` referenced `vscreenout.val` but no matching question element existed.
**Fix:** Declare all variables as question elements before referencing them.
**Session:** 1 | **Commit:** `1653e66`

### Rule 8.3: Add explicit `value` attributes to `<row>` and `<col>` elements
**Error:** Rows without explicit `value` attributes caused mismatches when JS set radio inputs by value.
**Fix:** Always set explicit values:
```xml
<row label="r1" value="1">Democrat</row>
<row label="r2" value="2">Republican</row>
```
**Sessions:** 1, 2 | **Commit:** `a6d2017`

### Rule 8.4: `cond="0"` prevents DOM rendering — hidden rows won't have inputs
**Error:** Adding `cond="0"` to r98 PNTA rows prevented Decipher from rendering radio inputs in the DOM. Custom JS `setRadio(q, '98')` had nothing to target.
**Fix:** Remove `cond="0"` from rows that need native inputs. Use CSS (`.sc-native-hidden`) to visually hide them instead.
**Session:** 2 | **Commit:** `6020ef4`

### Rule 8.5: `<html>` elements do NOT support child `<title>` tags
**Error:** Child `<title>` tags inside `<html>` elements are not supported by Decipher.
**Fix:** Put all content inside the CDATA block, not as child elements.
**Session:** 3 | **Commit:** `3a02be4`

### Rule 8.6: `<html>` elements use CDATA content, not child `<style>` tags
**Error:** Using child `<style>` elements inside `<html>` instead of CDATA content caused rendering failures.
**Fix:** Use inline CDATA for all `<html>` element content.
**Session:** 3 | **Commit:** `26446d2`

### Rule 8.7: `where="execute"` on `<html>` elements prevents rendering
**Error:** `where="execute"` on MaxDiff intro `<html>` elements caused Decipher to skip rendering them entirely, creating blank page flashes.
**Fix:** Remove `where="execute"` from `<html>` elements that need to display content. The element renders in the survey flow by default.
**Session:** 3 | **Commit:** `a962162`

---

## 9. Survey Flow & Page Breaks

### Rule 9.1: Group questions sharing a custom UI on the same page
**Error:** A `<suspend/>` between QS5 and QS5A/QS5B split a single interactive card across pages.
**Fix:** No `<suspend/>` between questions managed by the same JS UI.
**Caution (from official docs):** Decipher's validation can **split same-page questions across screens** — if only some questions are answered, unanswered ones may appear alone on a follow-up screen. For dependent questions, the Survey Editor's "Keep With" option forces them to stay together during validation. In XML, this means dependent questions with shared JS/CSS should always be on the same page with no `<suspend/>` between them to avoid broken interactions when validation splits them.
**Session:** 1 | **Commit:** `f7e55e2` | **Source:** Official Forsta "Keeping Questions Together" docs

### Rule 9.2: Add `<suspend/>` before `<exec>` blocks that reference prior answers
**Error:** `<exec>` blocks need a server round-trip to access answer data from the previous page.
**Fix:** Place `<suspend/>` after questions and before `<exec>` blocks that read them.
**Session:** 1 | **Commit:** `1f77c24`

### Rule 9.3: Add `<suspend/>` between questions that should appear on separate pages
**Error:** NM_PLAT and NM_TOPICS appeared on the same page because no `<suspend/>` separated them.
**Fix:** Always insert `<suspend/>` between question groups that should render as separate pages.
**Session:** 4 | **Commit:** `b7f7e6e`

### Rule 9.4: Scope CSS hiding to specific pages, not globally
**Error:** `.nextPage, .button { display: none !important }` applied globally hid native Continue buttons on ALL pages, including MaxDiff and later sections.
**Fix:** Scope navigation hiding to specific page groups via wrapper classes or `with=` attributes.
**Session:** 3 | **Commit:** `e4227c0`

### Rule 9.5: Excessive `<suspend/>` tags create blank pages
**Error:** 15+ suspend tags from ZIP code processing created blank pages with hidden submit buttons, trapping respondents.
**Fix:** Only use `<suspend/>` where a visible page break is needed.
**Session:** 3 | **Commit:** `e4227c0`

---

## 10. Screening & Termination Logic

### Rule 10.1: Use `<exec>` with `setMarker()` for screening
```xml
<exec>
if QS1.r2 or QS1.r99:
    setMarker('Screened-QS1')
</exec>
<term label="Term_QS1" cond="hasMarker('Screened-QS1')">Thank you.</term>
```

### Rule 10.2: Use `cond=` (not `code=`) on `<exit>` elements
**Error:** `<exit code="qualified">` is not valid.
**Fix:** `<exit cond="qualified">`.
**Session:** 1 | **Commit:** `1f77c24`

### Rule 10.3: Consolidate `<exec>` blocks when practical
**Error:** Multiple separate `<exec>` blocks with `cond=` attributes caused Decipher validation issues in Session 2.
**Note:** Per official Forsta docs, `cond` IS a valid attribute on `<exec>` (see Rule 20.3). The validation issues may have been context-specific. However, consolidating into a single `<exec>` is still cleaner and avoids edge cases:
```xml
<exec>
if QS1.r2 or QS1.r99:
    setMarker('Screened-QS1')
if QVOTE24.r4 or QVOTE24.r98:
    setMarker('Screened-QVOTE24')
</exec>
```
**Important:** `cond` is IGNORED when `when` is set to `started`, `finished`, `returning`, `submit`, or `verified` (see Rule 20.3).
**Session:** 2 | **Commit:** `9ad77b8`

### Rule 10.4: Verify termination conditions don't terminate eligible respondents
**Error:** A Term_PARTYID condition terminated respondents who were actually eligible for both typing models. Every VOTE x PARTY combination had a valid model assignment.
**Fix:** Map out all termination paths against the typing model assignment matrix before implementing.
**Session:** 2 | **Commit:** `5b70e49`

---

## 11. Native Input Interop — Radios

### Rule 11.1: Decipher radio input `value` formats vary — try multiple strategies
Native `<input>` elements may have values as:
1. Explicit numeric value (when `value="N"` is on `<row>`)
2. Row-label format: `r1`, `r2`, `r99`
3. Position-based (fallback)

**Fix:** Try row-label format FIRST (Decipher default), then numeric, then position:
```javascript
function setRadio(qId, val) {
    var box = findQ(qId);
    var inp = box.querySelector('input[value="r' + val + '"]')
           || box.querySelector('input[value="' + val + '"]');
    if (!inp) {
        var radios = box.querySelectorAll('input[type="radio"]');
        inp = radios[val - 1];
    }
    if (inp) { inp.click(); jQuery(inp).trigger('change'); }
}
```
**Sessions:** 1, 3 | **Commits:** `a6d2017`, `7115912`

### Rule 11.2: FIR (Form Image Replacement) replaces native radio/checkbox rendering
**Per official Forsta docs**, when `fir="on"` is set (globally or per-question), standard `<input type="radio">` and `<input type="checkbox">` browser inputs are replaced with SVG graphics. The underlying `<input>` elements still exist in the DOM but are visually hidden. Custom JS sync should:
- Still target the native `<input>` elements (they remain in the DOM)
- Trigger both native and jQuery events so FIR's visual state updates
- NOT rely on visible checkbox/radio appearance for state detection

FIR styles: `rounded` (default), `square`, `scale`, `fontawesome`/`fa`.
FIR can be disabled per-question with `fir="off"`.
**Source:** Official Forsta "Modifying Form Buttons" documentation

### Rule 11.3: Always dispatch BOTH native and jQuery events
**Error:** Using only `jQuery.trigger('click')` fired jQuery handlers but not Decipher's native event listeners. Using only native `.click()` missed jQuery-bound handlers.
**Fix:** Use both:
```javascript
inp.click();                              // native
inp.dispatchEvent(new Event('change', {bubbles:true}));  // native
jQuery(inp).trigger('change');            // jQuery
```
**Sessions:** 3, 4 | **Commits:** `91d6d99`, `44ed2bb`

### Rule 11.4: Watch for off-by-one between custom UI values and Decipher radio indices
**Error:** Custom UI `data-val="1"` meaning "first answer" but Decipher radios were 0-indexed. Value-matching selected the WRONG answer, causing incorrect terminations.
**Fix:** Use position-based selection: `data-val="1"` → `radios[0]` (index 0).
**Session:** 3 | **Commit:** `430e576`

---

## 12. Native Input Interop — Checkboxes

### Rule 12.1: Decipher checkboxes always have `value="1"` — the `name` encodes the row
**Per official Forsta docs**, the `el.checkbox` style renders:
```html
<input type="checkbox" name="$(name)" id="$(id)" value="1" class="input checkbox" />
```
ALL checkbox inputs have `value="1"`. The row identity is encoded in the `name` attribute, NOT the `value`. This means value-based matching (`input[value="r3"]`) will NEVER work for checkboxes.
**Source:** Official Forsta `el.checkbox` style template

### Rule 12.2: NEVER use `.click()` after setting `.checked` on checkboxes
**Error:** Setting `inp.checked = true` then calling `inp.click()` toggled the checkbox BACK to false. Decipher saw no selections and blocked page advance. This was the single most repeated error across sessions 2, 3, and 4.
**Fix:** Only call `.click()` when state needs to CHANGE:
```javascript
if (inp.checked !== desiredState) {
    inp.click();
}
jQuery(inp).trigger('change');
```
**Sessions:** 2, 4 | **Commits:** `0aa6c19`, `440e149`, `e25637c`, `45ee317`

### Rule 12.3: Use `trigger('change')` NOT `trigger('click')` for checkbox sync
**Error:** `jQuery(cb).trigger('click').trigger('change')` inverted checkbox state. The `trigger('click')` toggles the checkbox.
**Fix:** Use only `trigger('change')` after setting `.checked`:
```javascript
cb.checked = true;
jQuery(cb).trigger('change');
```
**Session:** 4 | **Commits:** `45ee317`, `440e149`

### Rule 12.4: Name-based substring matching (`name*=`) causes cross-row collisions
**Error:** Searching for `input[name*="r1"]` matched r1, r10, r11, r12, r13, r14.
**Fix:** Use exact match: `name === qLabel + '_' + rowLabel` or use the `ans{id}` prefix convention (see Rule 14).
**Session:** 4 | **Commit:** `0aa6c19`

---

## 13. Native Input Interop — Ratings & Selects

### Rule 13.1: Decipher may render hidden rating questions as `<select>` dropdowns, not radios
**Error:** `nmSyncRating` only searched for `input[type="radio"]` elements, but Decipher rendered hidden `<radio type="rating">` questions as `<select>` dropdowns. ALL source ratings silently failed.
**Fix:** After exhausting radio strategies, check for `<select>` elements:
```javascript
// Strategy: find select by name
var selects = box.querySelectorAll('select');
for (var i = 0; i < selects.length; i++) {
    if (selects[i].name.indexOf(rowLabel) >= 0) {
        selects[i].value = colVal;
        selects[i].dispatchEvent(new Event('change', {bubbles:true}));
        break;
    }
}
```
**Session:** 4 | **Commit:** `66c0ee0`

### Rule 13.2: Position-based fallback must handle high row numbers
**Error:** Strategy checking `numGroups >= rowNumber` failed for high rows (e.g., r39 when only 17 radio groups existed).
**Fix:** Match by name suffix instead of position index. For row `rN`, look for inputs whose name ends in `.{N-1}`:
```javascript
// r39 → look for name ending in ".38"
var suffix = '.' + (parseInt(rowLabel.replace('r','')) - 1);
```
**Session:** 4 | **Commit:** `6d97444`

### Rule 13.3: indexOf matching causes r1 to match r10, r11, etc.
**Error:** `name.indexOf('r1')` matched r1, r10, r11, r12... writing answers to wrong inputs and blocking form submission.
**Fix:** Use exact name match: `name === qLabel + '_' + rowLabel`.
**Session:** 4 | **Commit:** `ba6e2b0`

---

## 14. Decipher Input Naming Convention (ans{id})

### Rule 14.1: Decipher renders inputs as `ans{id}.0.{defIdx}` — not `qLabel_rowLabel`
**Error:** All 5 sync strategies (value match, name match, position, scan-all, text-based) failed because Decipher actually renders checkbox inputs as `ans{id}.0.{idx}` with `value="1"`, not as `qLabel_rowLabel`.
**Fix:** Extract the `ans` prefix from any existing input, then construct the expected name:
```javascript
// Get prefix from first input in the question container
var firstInput = box.querySelector('input[type="checkbox"]');
var prefix = firstInput.name.replace(/\.\d+$/, '');  // e.g. "ans123456.0"
// For row rN (1-based), defIdx = N-1 (0-based)
var targetName = prefix + '.' + (N - 1);
var inp = box.querySelector('input[name="' + targetName + '"]');
```
**Session:** 4 | **Commits:** `e2512f6`, `0fc411c`

### Rule 14.2: Definition index is 0-based row definition order, NOT DOM order
**Error:** With `shuffle="rows"`, DOM position doesn't match definition order. Position-based matching broke after shuffling.
**Fix:** `rN` → `ans{id}.0.{N-1}` (the index is based on XML definition order, not display order). Search by name, not by DOM position.
**Session:** 4 | **Commit:** `0fc411c`

### Rule 14.3: Cache input lookups for performance
After resolving the correct input for a qLabel+rowLabel pair, cache it for O(1) subsequent lookups:
```javascript
var _cache = {};
function findInput(qLabel, rowLabel) {
    var key = qLabel + ':' + rowLabel;
    if (_cache[key]) return _cache[key];
    // ... lookup logic ...
    _cache[key] = inp;
    return inp;
}
```
**Session:** 4 | **Commit:** `e2512f6`

---

## 15. Form Submission & Navigation

### Rule 15.1: `ss:enableNavigation` controls the Back button — but may affect submit rendering
**Per official Forsta docs**, `ss:enableNavigation="1"` "adds a Back button to the survey." The Continue button (`button.continue`) should render regardless. However, in practice (Session 2), setting `ss:enableNavigation="0"` appeared to prevent `$('.nextPage').click()` from finding anything.
**Fix:** Use `ss:enableNavigation="1"` and hide the Back button with CSS if unwanted. The native Continue button (`id="btn_continue"`, `class="button continue"`) should always be present.
**Note:** The official `button.continue` template renders as:
```html
<input type="submit" name="continue" id="btn_continue" class="button continue" value="..." />
```
**Session:** 2 | **Commit:** `97dc987` | **Source:** Official Forsta `button.continue` style template

### Rule 15.2: Do NOT use `document.forms[0].submit()` — it bypasses Decipher handlers
**Error:** Direct form submission bypassed Decipher's validation, screening, and page-advance logic, causing JS error flashes and broken survey flow.
**Fix:** Always click Decipher's native submit button:
```javascript
var btn = document.querySelector('.nextPage')
       || document.querySelector('input.button')
       || document.querySelector('a.button')
       || document.querySelector('button[type="submit"]')
       || document.querySelector('[data-role="next"]');
if (btn) btn.click();
```
**Sessions:** 2, 3 | **Commits:** `c4bfd4d`, `97dc987`, `cab5d93`

### Rule 15.3: `type="submit" name="continue"` buttons bypass Decipher form handlers
**Error:** An ENJOY! button with `type="submit" name="continue"` directly submitted the HTML form, bypassing Decipher's native page-advance mechanism.
**Fix:** Use `type="button"` and programmatically click the hidden native Next button.
**Session:** 3 | **Commit:** `cab5d93`

### Rule 15.4: Broaden submit button selectors — Decipher renders them inconsistently
**Error:** Decipher may render submit buttons as `<a class="button">`, `<button>`, `<input class="button">`, or inside `.controlbarContainer`.
**Fix:** Use a fallback chain (includes official `btn_continue` ID):
```javascript
var btn = document.getElementById('btn_continue')
       || document.querySelector('.nextPage')
       || document.querySelector('input.button.continue')
       || document.querySelector('input.button')
       || document.querySelector('a.button')
       || document.querySelector('button[type="submit"]')
       || document.querySelector('[data-role="next"]');
```
**Session:** 4 | **Commit:** `c7ced29` | **Source:** Official Forsta `button.continue` template (`id="btn_continue"`)

### Rule 15.5: Hidden `display:none !important` buttons may not fire when clicked
**Error:** Clicking a button hidden with `display:none !important` via inline CSS doesn't override the `!important` in the stylesheet.
**Fix:** Use `setAttribute('style', 'display:block!important')` before clicking, or use `visibility:hidden` instead.
**Session:** 3 | **Commit:** `91d6d99`

---

## 16. Samplesources & Exit Pages

### Rule 16.1: Include `<samplesources>` with standard exit pages
```xml
<samplesources default="0">
  <samplesource list="0">
    <title>Open Survey</title>
    <exit cond="qualified"><b>Thank you for completing the survey!</b></exit>
    <exit cond="terminated"><b>Thank you for your time.</b></exit>
    <exit cond="overquota"><b>Thank you for your time.</b></exit>
  </samplesource>
</samplesources>
```
**Session:** 1 | **Commit:** `76a2210`

### Rule 16.2: Do NOT use `after="..."` referencing non-existent labels
**Error:** `after="Flag_prism"` referenced a label that didn't exist.
**Fix:** Remove dangling `after=` references.
**Session:** 1 | **Commit:** `76a2210`

---

## 17. Theme References & Themevars

### Rule 17.1: Only reference themes that exist on the target instance
**Error:** `theme="frozen:user/116957/dpi_project_temp"` caused survey termination when theme didn't exist.
**Fix:** Remove the `theme` attribute if unavailable. Verified across multiple sessions.

**Per official Forsta docs**, the `theme` attribute on `<survey>` accepts these values:

| Value | Type | Resolves To |
|-------|------|-------------|
| `system/[name]` | System theme | `/static/nthemes/system/themes/[name]/theme.less` |
| `company/[name]` | Company theme | `[company-path]/themes/[name]/theme.less` |
| `user/[id]/[name]` | User theme | `[company-path]/themes/users/[id]/[name]/theme.less` |
| `survey` | Survey-specific | `[project-path]/static/theme.less` |
| `frozen:[original]` | Frozen (live) | `[project-path]/static/theme.less` (copied from original) |

**Important:** When a survey goes live, its theme is "frozen" — the `theme.less` file is copied into the project's `/static` directory. This prevents live surveys from being affected by theme updates.
**Warning:** If using a custom `theme.less` file with `ss:includeLESS`, use `theme="survey"` or rename the file — otherwise going live will **overwrite** your custom `theme.less`.
**Sessions:** 1, 3 | **Commits:** `1f77c24`, `9395da2` | **Source:** Official Forsta "Editing the Survey Theme" docs

### Rule 17.2: FIR themevars provide native form input styling without custom CSS
**Per official Forsta docs**, FIR (Form Image Replacement) can be styled via themevars, avoiding the need for custom CSS to style radio/checkbox inputs:
```xml
<themevars>
  <themevar name="fir-border">#c7c7c7</themevar>
  <themevar name="fir-inner">#FFFFFF</themevar>
  <themevar name="fir-inner-hover">#8DDCDC</themevar>
  <themevar name="fir-inner-selected">#1CBAB9</themevar>
  <themevar name="fir-radio">circle-o</themevar>
  <themevar name="fir-radio-selected">dot-circle-o</themevar>
  <themevar name="fir-checkbox">square-o</themevar>
  <themevar name="fir-checkbox-selected">check-square</themevar>
</themevars>
```
Use `fir="on"` on the `<survey>` tag with `firStyle="rounded"`, `"square"`, `"scale"`, or `"fa"` (Font Awesome).
**Note:** This is a safer alternative to custom CSS for styling form inputs (avoids `@keyframes`, `var()`, and other CDATA issues from Rules 18.1–18.5).
**Source:** Official Forsta "Modifying Form Buttons" documentation

### Rule 17.3: Do NOT put `@`-containing URLs in `<themevars>`
**Error:** Google Fonts URL (`wght@400;500;600;700`) in a `webfont` themevar was parsed as Less variable references, causing a Less compile error.
**Fix:** Load fonts via `<link>` tags in `respview.client.css` instead of themevars.
**Session:** 4 | **Commit:** `887f9ec`

### Rule 17.4: Do NOT leave themevars empty — remove them entirely
**Error:** An empty `webfont` themevar caused `.webfontImport` mixin to fail with `@url undefined`.
**Fix:** Remove the themevar entirely rather than setting it to blank.
**Session:** 4 | **Commit:** `d720287`

### Rule 17.5: Multiple themes per survey using `<themes>` (compat 137+)
**Per official Forsta docs**, you can apply different themes conditionally using `<themes>` and `<theme>` tags:
```xml
<themes>
  <theme cond="list == '1'" name="system/education"/>
  <theme cond="list == '2'" name="company/company_theme"/>
  <theme cond="list == '3'" name="user/1/user_generated_theme"/>
  <theme cond="list == '4'" name="survey"/>
</themes>
```
Requirements:
- **Compat level 137+** required
- `name` must reference theme names from the Theme Editor (NOT file paths)
- `cond` uses standard Python condition syntax
- Themes are applied when the `<themes>` tag is evaluated
- Company/user themes require a `selfserve` directory
- Survey-specific themes must also be in the `<survey>` tag

**Tip:** Apply a theme via the Theme Editor first to get the correct `name` value, then copy it to the `<themes>` tag.
**Source:** Official Forsta "Editing the Survey Theme" docs

### Rule 17.6: Custom theme.less files can be exported, edited, and re-imported
The Theme Editor supports exporting `theme.less` files for programmatic customization. After editing with a text editor (see "The Less Styles System" for syntax), re-import via the Theme Editor. The file is compiled on upload — Less syntax errors will prevent application and show an error message.
**Naming:** Theme names inside the `.less` file must be alphanumeric — other characters are stripped on import.
**Source:** Official Forsta "Editing the Survey Theme" docs

---

## 18. CSS Content Restrictions

### Rule 18.1: No `@keyframes` in Decipher style blocks
**Error:** `@` prefix interpreted as template directive (`@if`, `@for`), crashing the template engine. **Confirmed by official docs:** `\@if`, `\@else`, `\@endif`, `\@for`, `\@end` are documented flow control directives in style blocks.
**Fix:** Use CSS `transition` properties instead.
**Session:** 1 | **Commit:** `8411c7a` | **Confirmed:** Forsta XML Style System docs, Section 1

### Rule 18.2: No `@media` queries in global CSS CDATA blocks
**Error:** `@media` rule caused NLPPL fatal error. Decipher's XML parser may not support it.
**Fix:** Avoid `@media` queries. Use fixed layouts or handle responsiveness via JS.
**Session:** 4 | **Commit:** `8fd5f44`

### Rule 18.3: Avoid CSS custom properties (`var()`)
**Error:** `var()` flagged as potential crash trigger.
**Fix:** Hard-code values directly.
**Session:** 1 | **Commit:** `c632e09`

### Rule 18.4: Avoid `-webkit-` vendor prefixes
**Error:** Identified as crash trigger during binary-search debugging.
**Fix:** Omit unless absolutely necessary.
**Session:** 1 | **Commit:** `c632e09`

### Rule 18.5: The `@` character is unsafe in ALL Decipher CDATA contexts
The `@` character is parsed by Decipher's template engine (CSS) and Less compiler (themevars). Avoid `@keyframes`, `@media`, `@import`, and `@`-containing URLs in any Decipher-processed content.
**Sessions:** 1, 4 | **Commits:** `8411c7a`, `8fd5f44`, `887f9ec`

---

## 19. DOM Element IDs

### Rule 19.1: The official question container ID is `question_LABEL`
**Per official Forsta docs**, the `question.header` style template renders:
```html
<div id="question_${this.label}" class="question ...">
```
So the canonical format is `question_LABEL` (e.g., `question_QS1`). However, Session 3 found `q_LABEL` on their instance — possibly due to a different theme, compat level, or DQ style override.
**Fix:** Try the official format first, then fall back:
```javascript
function findQ(label) {
    return document.getElementById('question_' + label)
        || document.getElementById('q_' + label)
        || document.getElementById(label)
        || document.querySelector('[id$="_' + label + '"]');
}
```
**Sessions:** 1, 3 | **Commits:** `8411c7a`, `b32bde8`, `eb036a7` | **Source:** Official Forsta `question.header` style template

**Double confirmation:** The FIR docs also use `#question_QQQ` as the selector pattern:
```javascript
$("#question_QQQ .cell").addClass("no-uncheck");
```

### Rule 19.2: `[rel ...]` pipe may not resolve inside `<html>` CDATA
**Fix:** Use absolute URLs or inline content instead.
**Session:** 1 | **Commit:** `8411c7a`

---

## 20. Exec Blocks & Python Logic

### Rule 20.1: Guard attribute access with `hasattr()` for draft/jump testing
**Error:** In DRAFT mode, jumping to pages skips `<exec>` blocks that initialize variables, causing `AttributeError: 'PersistentDict' object has no attribute 'maxdiff1'`.
**Fix:**
```python
if not hasattr(p, 'maxdiff1'):
    p.maxdiff1 = []
```
**Tip (from official docs):** Use `when="flow"` to set default values for persistent variables that would cause errors in "One Page" test mode.
**Session:** 4 | **Commit:** `773cd70`

### Rule 20.2: `when="init"` CANNOT access question content or participant data
**Per official Forsta docs:** "There is no participant information at this point, so you cannot access extra variables nor can you modify or access question content."
`when="init"` is appropriate for:
- Initializing databases (`File()`, `Database()`)
- Defining global variables and lists
- Creating functions to be used survey-wide

It is NOT appropriate for:
- Setting question values (`Q1.val = ...`)
- Modifying question titles (`Q1.title = "..."`)
- Accessing extra variables

**Fix for design file loading:** Keep as `when="init"` for `File()` calls (correct usage). But do not attempt to access `p.*` or question data.
**Session:** 3 | **Commits:** `c5c788c`, `a042059` | **Confirmed by:** Official Forsta Exec Tag docs

### Rule 20.3: The `<exec>` tag has 13 `when` values — use the right one

| `when` Value | When It Runs | Can Access Questions? | `cond` Respected? |
|---|---|---|---|
| `survey` (default) | When participant reaches that location | Yes | Yes |
| `started` | First time participant enters survey | Yes | **No** |
| `init` | Once when survey is loaded | **No** | Yes |
| `virtualInit` | When running reports for virtual questions | **No** | Yes |
| `finished` | After submit, before results written | Yes | **No** |
| `returning` | When participant returns from redirect | Yes | **No** |
| `verified` | Each time participant submits valid data | Yes | **No** |
| `virtual` | Once per participant for virtual questions | Yes | Yes |
| `flow` | When "One Page" test mode is toggled | Yes | Yes |
| `submit` | Each time Continue/Finish is clicked | Yes | **No** |
| `sqlTransfer` | When copying SQL data to results.bin | Special | Yes |
| `sqlTransferInit` | Initializes data for sqlTransfer | Special | Yes |
| `autosaveRestored` | When participant re-enters after exit (delphi="1" only) | Yes | Yes |

**Critical:** `cond` is IGNORED when `when` is set to `started`, `finished`, `returning`, `submit`, or `verified`.
**Source:** Official Forsta Exec Tag documentation

### Rule 20.4: Non-ASCII and special characters must be escaped in `<exec>` strings
**Per official Forsta docs:** "Non-ASCII characters are not allowed in strings within an exec block. The following characters `<`, `>`, `[`, `]`, `"`, `&`, and `'` must be escaped in strings within an exec block."

This means:
- **No em dashes, smart quotes, or Unicode** in exec block strings (confirms Rule 3.2)
- **Square brackets `[]` must be escaped** — even in Python strings inside exec blocks
- **Angle brackets `<>` must be escaped** — use CDATA wrapping (Rule 1.3) or avoid in strings
- **Ampersand `&` and quotes `"` `'` must be escaped**

**Fix:** Use CDATA wrapping for exec blocks with comparison operators, and avoid special characters in string literals:
```xml
<exec><![CDATA[
if col < len(groups):
    msg = "value is less than expected"
]]></exec>
```
**Sessions:** 1, 3 | **Commits:** `082b133`, `9fde39e` | **Confirmed by:** Official Forsta Exec Tag docs

### Rule 20.5: `where="execute"` is the standard pattern for hidden computed questions
**Per official Forsta docs**, hidden questions that compute values should use `where="execute"`:
```xml
<radio label="vAge" where="execute">
  <exec>
  for eachRow in vAge.rows:
      age_range = eachRow.o.alt
      if Q1.check(age_range):
          vAge.val = eachRow.index
          break
  </exec>
  <title>Age Group (Hidden)</title>
  <row label="r1" alt="1-17">1-17</row>
  <row label="r2" alt="18-24">18-24</row>
</radio>
```
Note: An `<exec>` block can be nested INSIDE a question element with `where="execute"` to compute its value. The `.val` and `.index` properties are the standard way to set values.
**Source:** Official Forsta Exec Tag documentation
**See also:** Rule 8.1 (correction)

### Rule 20.6: Skip header rows in `.dat` design files
**Error:** First line of `.dat` files contained column names (Version, Set, Item1...) creating a junk dictionary key.
**Fix:** Skip the header row when parsing.
**Session:** 3 | **Commit:** `c5c788c`

### Rule 20.7: Case-sensitive filenames matter
**Error:** `DEMDesign.dat` referenced in code but actual file was `DemDesign.dat`.
**Fix:** Match exact case of uploaded filenames.
**Session:** 3 | **Commit:** `9da8417`

### Rule 20.8: Python question object API — complete attribute reference
**Per official Forsta "Python Expressions" docs**, all question objects (elements with a `label`) support these attributes via the dot operator:

**Question-level attributes:**
| Attribute | Returns | Notes |
|-----------|---------|-------|
| `Q.label` | Question label string | `"Q10"` |
| `Q.title` | Question title (settable) | Can be modified dynamically |
| `Q.val` | Selected value or `None` | For single-value questions only |
| `Q.ival` | Value or `0` (never `None`) | Best for `<number>`/`<float>` math |
| `Q.unsafe_val` | Raw value without HTML encoding | **Never output to HTML** |
| `Q.selected` | Selected row/col object or `None` | Equivalent to `Q.rows[Q.val]` |
| `Q.rows` | List of row objects | Iterable: `for r in Q.rows:` |
| `Q.cols` | List of col objects | Iterable: `for c in Q.cols:` |
| `Q.choices` | List of choice objects | For `<select>` questions |
| `Q.attr('r1')` | Access cell by label string | Equivalent to `Q.r1` |
| `Q.map(r1=5, r2=10)` | Remap selected value | Returns mapped value |
| `Q.disabled` | Hide question (settable) | `Q.disabled = True` |
| `Q.displayed` | `True` if visible (not disabled, cond is True) | Read-only; ignores `where=` |
| `Q.atleast` | Min selections (settable) | Dynamic validation |
| `Q.atmost` | Max selections (settable) | Dynamic validation |
| `Q.exactly` | Exact selections (settable) | Dynamic validation |
| `Q.points` | Points total (settable) | For `<number>` questions |
| `Q.amount` | Amount total (settable) | For `<number>` questions |
| `Q._q` | Raw question object (read-only!) | **Not available in secure surveys** |
| `Q.o` | Raw question object (read-only!) | Works in secure surveys |

**Cell-level attributes** (rows, cols, choices):
| Attribute | Returns | Notes |
|-----------|---------|-------|
| `Q.r1.label` | Cell label string | `"r1"` |
| `Q.r1.index` | Cell index (0-based) | |
| `Q.r1.text` | Cell text/title | |
| `Q.r1.val` | Cell value or `None` (settable) | |
| `Q.r1.ival` | Cell value or `0` (read-only) | Never assign to `.ival` |
| `Q.r1.value` | Data file value (from `value="..."` attr) | |
| `Q.r1.empty` | `True` if `None` or blank | |
| `Q.r1.open` | Open-ended text (settable) | For `open="1"` rows |
| `Q.r1.unsafe_open` | Raw open text without HTML encoding | **Never output to HTML** |
| `Q.r1.disabled` | Hide cell (settable) | `Q.r1.disabled = True` |
| `Q.r1.displayed` | `True` if visible | |
| `Q.r1.inrange(min, max)` | `True` if value in range (inclusive) | |
| `Q.r1.map(c1=5, c2=10)` | Remap 2D cell value | |
| `Q.r1.group` | Cell's primary group object | `.group.label`, `.group.text` |
| `Q.r1.c1` | 2D cell access | For grid questions |

**Common patterns:**
```python
# Iterate rows and set values
for eachRow in Q10.rows:
    eachRow.val = eachRow.text

# Dynamic validation
Q10.exactly = 2

# Remap values
Q11.val = Q10.map(r1=1, r2=3, r3=5)

# Check if answered
if Q10.r1.empty:
    pass  # no answer for r1

# Access selected item
if Q10.selected:
    print Q10.selected.label  # e.g. "r2"
    print Q10.selected.text   # e.g. "Item 2"

# Range check
if Q10.r1.inrange(1, 100):
    pass  # value between 1 and 100

# 2D grid access
print Q10.r1.c1  # True/False for checkbox grid
print Q10.r1.c2.val  # value for number grid
```
**Source:** Official Forsta "Python Expressions" documentation

---

## 21. Comments

### Rule 21.1: Use `<note>` — HTML comments are NOT supported
**Error:** `<!-- -->` comments caused XML parse errors in the Survey Editor.
**Fix:** `<note>This is a comment</note>`
**Sessions:** 3, 4 | **Commits:** `09ac5f2`, `1addf75`

---

## 22. Quota Management

### Rule 22.1: Quota sheets must exist on the server before `<quota>` tags will compile
**Error:** `<quota>` tags referencing non-existent sheets (TYPING MODULE Quota, Dem Quota, GOP Quota) caused overquota terminations — respondents hit `<exit cond="overquota">`.
**Fix:** Create quota sheets in the Decipher quota editor before adding `<quota>` tags to the XML.
**Session:** 3 | **Commits:** `082b133`, `fce35d1`, `ca7026b`

### Rule 22.2: Quotas must be defined in Excel files, not inline `<cell>` elements
**Error:** Inline `<cell>` elements inside `<quota>` tags caused "Name not defined as expression or marker" errors.
**Fix:** Define quotas in a separate `.xlsx` file uploaded to the Decipher server with proper sheets.
**Session:** 3 | **Commits:** `5d9d397`, `9b45904`

### Rule 22.3: Include `setup="quota"` in `<survey>` when using quotas
**Error:** Removing `quota` from the `setup` attribute broke quota-based version assignment.
**Fix:** Keep `setup="term,decLang,quota,time"` when quotas are in use.
**Session:** 3 | **Commit:** `ca7026b`

---

## 23. Design File Loading

### Rule 23.1: `.dat` files must be uploaded to the survey directory
**Error:** Design file loading returned empty dicts because files weren't found.
**Fix:** Upload `.dat` files to the survey's file directory on the Decipher server.
**Session:** 3 | **Commits:** `3bd5edb`, `6576437`

### Rule 23.2: Use descriptive error messages for missing design files
**Error:** Missing `.dat` files caused cryptic "key not found, available keys: (empty)" errors.
**Fix:** Check file existence and log available files before attempting to parse.
**Session:** 3 | **Commit:** `3bd5edb`

---

## 24. HTML Element Restrictions

### Rule 24.1: Zero JS on `<html>` intro pages — restyle native Decipher navigation instead
**Error:** Any JavaScript with bracket notation in `<html>` CDATA crashed due to variable substitution. After 8+ attempts to fix bracket-free JS in intro pages, the solution was to eliminate JS entirely.
**Fix:** Use CSS-only approach — restyle Decipher's native Next button to match design (e.g., make it look like an "ENJOY!" button).
**Session:** 3 | **Commit:** `678d44d`

### Rule 24.2: For complex custom UI, prefer native Decipher widgets over custom JS
**Error:** Hundreds of lines of custom CSS/JS/HTML overlay for checkboxes, rating scales, and card ratings led to sync bugs, checkbox inversions, and silent data loss.
**Fix:** Use native Decipher widgets with `<themevars>` for styling:
- Checkboxes: `<checkbox>` with `groups` pattern for exclusive "None"
- Buttons: `<radio type="select" uses="atm1d.11">` for tiled buttons
- Card ratings: `<radio type="rating" uses="cardrating.1">`
**Session:** 4 | **Commits:** `414c190`, `ad07f4d`

---

## 25. Style Block Naming

### Rule 25.1: Valid `<style name="...">` values — exhaustive list from official docs

**Page-level styles** (nest anywhere in `<survey>`, NOT inside questions):

| Style Name | Purpose |
|------------|---------|
| `global.page.head` | Extra HTML in `<head>` globally |
| `respview.client.meta` | Additional `<meta>` tags |
| `respview.client.css` | Custom CSS after default CSS in `<head>` |
| `respview.client.js` | Custom JS after default JS in `<head>` |
| `survey.header` | Header before survey content and logo |
| `survey.logo` | Survey logo display |
| `buttons` | Button container at bottom of page |
| `button.continue` | The "Continue" button |
| `button.finish` | The "Finish" button (last page) |
| `button.cancel` | Extra button (blank by default) |
| `button.goback` | Back button (requires `ss:enableNavigation="1"`) |
| `survey.completion` | Progress bar |
| `survey.respview.footer` | Footer at end of survey page |
| `survey.respview.footer.support` | Support links in footer |
| `page.head` | Per-page `<head>` additions |

**Question-level styles** (nest inside question tags):

| Style Name | Purpose |
|------------|---------|
| `question.header` | Start of question (title, errors, instructions) |
| `question.footer` | End of question |
| `question.after` | Blank — use with `wrap="ready"` for JS after question |
| `survey.question` | Question text display |
| `survey.question.instructions` | Instruction text display |
| `survey.question.answers.start` | Start of answer table |
| `survey.question.answers.end` | End of answer table |
| `question.row` | Row containing legend + input element |
| `question.top-legend` | Column legend row (top) |
| `question.top-legend-item` | Individual column legend cell |
| `question.bottom-legend` | Column legend row (bottom) |
| `question.bottom-legend-item` | Individual bottom legend cell |
| `question.col-legend-row` | Repeated column legends |
| `question.col-legend-row-item` | Individual repeated legend cell |
| `question.left` | Left row legend text |
| `question.right` | Right row legend text |
| `question.left-blank-legend` | Blank cell left of top legend |
| `question.right-blank-legend` | Blank cell right of top legend |
| `question.group` | Row group heading (depth 1) |
| `question.group-2` | Row group heading (depth 2) |
| `question.group-3` | Row group heading (depth 3) |
| `question.group-column` | Column group heading row |
| `question.group-column-cell` | Individual column group cell |
| `question.na.row` | Noanswer row |
| `question.element` | Answer cell with input element |

**Element-level styles** (input rendering):

| Style Name | Purpose |
|------------|---------|
| `el.radio` | Single-select radio input |
| `el.checkbox` | Multi-select checkbox input |
| `el.select.header` | Start of dropdown |
| `el.select.default` | Default "Select..." option |
| `el.select.element` | Dropdown choice option |
| `el.select.footer` | End of dropdown |
| `el.text` | Text/number input field |
| `el.textarea` | Multi-line text input |
| `el.noanswer` | Noanswer checkbox |
| `el.open` | Open-ended input in rows |
| `el.image` | File upload input |

**NOT valid:** `survey.footer`, `survey.respview`, or any arbitrary name not in the list above.

**Session:** 4 | **Commits:** `a22061b`, `63fdc4f`, `8c79241` | **Source:** Official Forsta XML Style System documentation

---

## 26. Conditional Row Visibility

### Rule 26.1: Filter hardcoded item arrays against DOM at runtime
**Error:** Hardcoded item arrays included rows conditioned out by `cond=` on `<row>` elements (e.g., GOP-only items hidden for DEM respondents). Custom UI showed tiles with no backing native input, causing "NO INPUT FOUND" errors and silent data loss.
**Fix:** Filter items against inputs that actually exist in the DOM:
```javascript
items = items.filter(function(item) {
    var box = nmFindQ(qLabel);
    return box && box.querySelector('input[name*="' + item.row + '"], select[name*="' + item.row + '"]');
});
```
**Sessions:** 4 | **Commits:** `2b1c3dc`, `e9277a0`, `be45b52`

### Rule 26.2: Prefer hardcoded arrays + DOM filtering over DOM scraping
**Error:** `nmGetRows()` DOM scraping failed to extract row names reliably, causing blank swipe cards. Reverted to hardcoded arrays.
**Fix:** Use hardcoded arrays for reliable text content, but filter against DOM inputs to respect runtime `cond=` filtering.
**Session:** 4 | **Commits:** `bcd445b`, `1ebccd9`

---

## Error History Summary — All Sessions

### Session 1: Initial Build (`master`, 31 commits)

| # | Error / Symptom | Root Cause | Rule |
|---|-----------------|------------|------|
| 1 | WKDFJ save error | Duplicate `<?xml?>` declaration | 1.1 |
| 2 | WKDFJ save error | Unquoted attribute values | 1.2 |
| 3 | Validation error | Undeclared `vscreenout` variable | 8.2 |
| 4 | XSVJV fatal error | `where="execute"` on `<text>` | 8.1 |
| 5 | XSVJV/DBNZJ fatal error | Non-ASCII emoji in CDATA | 3.1 |
| 6 | Server crash | Dangling `after="Flag_prism"` ref | 16.2 |
| 7 | CDATA parse corruption | `</style>` tag-name collision | 5.1 |
| 8 | Save crashes (7 bisect commits) | `@keyframes`, `var()`, `-webkit-` | 18.1–18.4 |
| 9 | Namespace "redefined" | `xmlns:builder` declared manually | 2.1 |
| 10 | Theme not found | Invalid `theme=` reference | 17.1 |
| 11 | Invalid `code=` on `<exit>` | Should be `cond=` | 10.2 |
| 12 | "Variable 0-9 not set" | `pattern="[0-9]*"` brackets | 4.2 |
| 13 | Variable substitution crash | `input[type="submit"]` in `<html>` | 4.3 |
| 14 | CSS not loading | Extra `<style type="text/css">` | 6.2 |
| 15 | No interactions | Zero JavaScript | 7.1 |
| 16 | JS not executing | `<script>` inside `<html>` CDATA | 7.3 |
| 17 | CSS/JS not loading | Wrong style block structure | 6.1, 7.1 |
| 18 | @keyframes crash | `@` = template directive | 18.1 |
| 19 | CSS/JS wrong IDs | `q_LABEL` vs `question_LABEL` | 19.1 |
| 20 | Termination not firing | Native inputs not set | 11.1 |

### Session 2: PNTA & Navigation (`fix-pnta-checkbox`, 9 commits)

| # | Error / Symptom | Root Cause | Rule |
|---|-----------------|------------|------|
| 21 | PNTA not saving | r98 rows had `cond="0"` — no inputs in DOM | 8.4 |
| 22 | Eligible respondents terminated | Incorrect Term_PARTYID condition | 10.4 |
| 23 | Continue button non-functional | `ss:enableNavigation="0"` removed submit infra | 15.1 |
| 24 | Form submit bypassed handlers | `document.forms[0].submit()` used | 15.2 |
| 25 | `[four / five]` variable error | Brackets in display text | 4.5 |

### Session 3: MaxDiff Implementation (`maxdiff-xml-implementation`, 57 commits)

| # | Error / Symptom | Root Cause | Rule |
|---|-----------------|------------|------|
| 26 | Page progression blocked | Global CSS hiding native Continue buttons | 9.4 |
| 27 | 15+ blank pages | Excessive `<suspend/>` tags | 9.5 |
| 28 | setRadio selecting wrong input | Numeric value matched wrong radio | 11.1 |
| 29 | jQuery events not reaching Decipher | `trigger('click')` only fires jQuery handlers | 11.3 |
| 30 | Data capture failing | `question_` prefix vs actual `q_` prefix | 19.1 |
| 31 | Off-by-one termination | `data-val="1"` matched 0-indexed radio value "1" (2nd answer) | 11.4 |
| 32 | `<!-- -->` comments rejected | HTML comments not supported | 21.1 |
| 33 | ASCII exec error | Non-ASCII chars in `<exec>` blocks | 3.2 |
| 34 | Overquota termination | Quota sheets don't exist on server | 22.1 |
| 35 | "Name not defined" | Inline `<cell>` not valid for quotas | 22.2 |
| 36 | xmlns preventing save | Namespace declarations rejected | 2.3 |
| 37 | Design file empty dict | Header row parsed as data | 20.6 |
| 38 | `v3_t1 not found` | Case mismatch: `DEMDesign.dat` vs `DemDesign.dat` | 20.7 |
| 39 | Intro pages blank | `where="execute"` on `<html>` elements | 8.7 |
| 40 | ENJOY! button bypassed handlers | `type="submit" name="continue"` | 15.3 |
| 41 | `[type=submit]` in CDATA | Brackets in onclick handler | 4.1 |
| 42 | `c[0]` variable parse error | Array bracket access in `<html>` | 4.4 |
| 43 | `<title>` inside `<html>` | Unsupported child element | 8.5 |
| 44 | `<style>` children in `<html>` | Wrong content model | 8.6 |
| 45 | Theme causing termination | Non-existent frozen theme | 17.1 |
| 46 | `<html>` JS crashes | Brackets unavoidable in JS | 24.1 |

### Session 4: New Media & INF Refactor (`survey-new-media-section`, 55 commits)

| # | Error / Symptom | Root Cause | Rule |
|---|-----------------|------------|------|
| 47 | Checkbox inversion | `trigger('click')` toggled state back | 12.2 |
| 48 | Checkbox sync failure | `name*="r1"` matched r10–r14 | 12.4 |
| 49 | Rating sync ALL failing | Decipher renders ratings as `<select>`, not radios | 13.1 |
| 50 | Rating r1 matched r10 | `indexOf` substring match | 13.3 |
| 51 | Ratings lost for high rows (r39) | Position fallback inadequate for high-numbered rows | 13.2 |
| 52 | 5 sync strategies all failed | Inputs named `ans{id}.0.{defIdx}`, not `qLabel_rowLabel` | 14.1 |
| 53 | Shuffle broke position matching | `defIdx` ≠ DOM position | 14.2 |
| 54 | `survey.footer` not valid | Unsupported style name | 25.1 |
| 55 | `survey.respview` not valid | Unsupported style name | 25.1 |
| 56 | Conditioned-out rows in custom UI | Items shown but no backing native input | 26.1 |
| 57 | Blank swipe cards | `nmGetRows()` DOM scraping failed | 26.2 |
| 58 | `</style>` collision in mode="before" | Inner style tag closed outer element | 5.2 |
| 59 | `&rsquo;` parse error | Named entities not safe in CDATA | 3.3 |
| 60 | NLPPL fatal error | `@media` query in global CSS | 18.2 |
| 61 | XML parse error at line 2350 | Bare `<` operator in `<exec>` | 1.3 |
| 62 | Less `@url undefined` | `@` in Google Fonts URL parsed as Less variable | 17.3 |
| 63 | Less mixin error | Empty webfont themevar | 17.4 |
| 64 | `with=` styles not applying | Invalid question labels in `with=` attribute | 6.4 |
| 65 | 6 reverts in one session | Custom JS too fragile — switched to native widgets | 24.2 |
| 66 | Missing `<suspend/>` | NM_PLAT and NM_TOPICS on same page | 9.3 |

---

## Debugging Methodology

### Binary Search for CDATA Crashes (Session 1)
When a CDATA block causes unexplained crashes, use progressive bisection:
1. **Minimal test** (`661c489`): Strip to 3 lines of CSS
2. **Add half** (`c632e09`): Add ~140 lines to find threshold
3. **Full CSS, no JS** (`063d634`): Isolate domain
4. **Progressive removal** (`5db0197` → `f47d084`): Remove sections one-by-one
5. **Restore baseline** (`2246abf` → `2f90af6`): Return to known-good and rebuild

### Revert-to-Baseline Pattern (Sessions 3, 4)
When incremental fixes compound into instability:
1. Identify last known-good commit
2. Revert to that state completely (`978d204`, `e3be13d`)
3. Apply ONE minimal change at a time
4. Test after each change

This was used 6 times in Session 4 alone, ultimately leading to the decision to replace custom JS with native Decipher widgets (Rule 24.2).

### When Custom JS Sync Is Unavoidable
If you must sync custom UI to native Decipher inputs, follow this priority order:
1. **Extract the `ans{id}` prefix** from any existing input in the question container
2. **Construct target name** from prefix + definition index: `ans{id}.0.{rowNumber - 1}`
3. **Search by exact name** — never substring or position
4. **Dispatch BOTH native and jQuery events** — `inp.click()` + `jQuery(inp).trigger('change')`
5. **Never `.click()` after `.checked = true`** on checkboxes
6. **Check for `<select>` elements** as well as `<input type="radio">`
7. **Filter items against DOM** to respect runtime `cond=` row filtering
8. **Cache lookups** to avoid repeated DOM traversal

---

## Quick Reference: Correct Decipher XML Skeleton

```xml
<?xml version="1.0" encoding="UTF-8"?>
<survey
  compat="146"
  delphi="1"
  state="testing"
  setup="term,decLang,quota,time"
  fir="on"
  firStyle="rounded"
  ss:enableNavigation="1"
  ss:hideProgressBar="1"
  html:showNumber="0"
  xmlns:html="http://www.w3.org/1999/xhtml"
  xmlns:ss="http://www.decipherinc.com/ss">

  <note>Resource strings</note>
  <res label="sys_noAnswerSelected">Please provide an answer.</res>

  <samplesources default="0">
    <samplesource list="0">
      <title>Open Survey</title>
      <exit cond="qualified"><b>Thank you!</b></exit>
      <exit cond="terminated"><b>Thank you for your time.</b></exit>
      <exit cond="overquota"><b>Thank you for your time.</b></exit>
    </samplesource>
  </samplesources>

  <note>Global CSS — raw HTML injected into head</note>
  <style name="respview.client.css" mode="after"><![CDATA[
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
  <style>
  /* CSS here — brackets ARE safe in this context */
  body { font-family: Inter, sans-serif; }
  </style>
  ]]></style>

  <note>Global JS — helper functions (no wrap=ready for global scope)</note>
  <style name="respview.client.js" mode="after"><![CDATA[
  <script>
  function findQ(label) {
      return document.getElementById('question_' + label)  // official format per Forsta docs
          || document.getElementById('q_' + label)          // alternate format seen in some instances
          || document.getElementById(label);
  }
  </script>
  ]]></style>

  <note>Page-scoped JS — runs in jQuery ready</note>
  <style name="respview.client.js" wrap="ready"><![CDATA[
  // jQuery is available as $ here
  ]]></style>

  <note>Custom HTML — NO brackets, NO script/style closing tags</note>
  <html label="survey_ui" where="survey"><![CDATA[
  <div id="sc-root">Custom UI here</div>
  ]]></html>

  <note>Questions with explicit row values</note>
  <radio label="Q1">
    <title>Question text</title>
    <row label="r1" value="1">Option 1</row>
    <row label="r2" value="2">Option 2</row>
  </radio>

  <suspend/>

  <note>Screening logic — single exec block</note>
  <exec>
  if Q1.r2:
      setMarker('Screened-Q1')
  </exec>
  <term label="Term_Q1" cond="hasMarker('Screened-Q1')">Thank you.</term>

</survey>
```

---

## 27. Official Forsta Reference Notes

> The following rules are derived from the official Forsta/Decipher documentation (Survey Tag attributes and XML Style System) and confirm, correct, or supplement the error-derived rules above.

### Rule 27.1: The `@` character is a template engine directive — confirmed by docs
The official docs confirm that style blocks support flow control via `\@if`, `\@else`, `\@endif`, `\@for`, `\@end`. This is why `@keyframes`, `@media`, and `@import` in CSS CDATA blocks crash the template engine — they are parsed as directives.
**Confirms:** Rules 18.1, 18.2, 18.5

### Rule 27.2: `[super]` inherits the default style in overrides
When overriding a style, `[super]` inserts the default style code at that position. `mode="before"` implicitly adds `[super]` at the beginning; `mode="after"` adds it at the end; `mode="instead"` replaces completely (no `[super]`).
**Note:** `[super]` is NOT the same as bracket variable substitution (Rule 4.1). It only works inside `<style>` blocks, not `<html>` CDATA.

### Rule 27.3: `<style mode="...">` has three values
| Mode | Behavior |
|------|----------|
| `instead` | Replaces the default style entirely |
| `before` | Prepends new code before the default (implicit `[super]` at end) |
| `after` | Appends new code after the default (implicit `[super]` at start) |

If no `mode` is specified, `instead` is the default behavior.

### Rule 27.4: `<style cond="...">` accepts Python conditions
A `<style>` element can have a `cond` attribute with Python code, evaluated at runtime. Useful for device-specific styles:
```xml
<style name="question.row" cond="gv.survey.root.mobile == 'compat'">
  <!-- mobile-specific row layout -->
</style>
```

### Rule 27.5: `<style>` supports `rows` and `cols` for targeted overrides
For question-level styles, `rows="r1,r3"` or `cols="c1,c2"` restricts the override to specific rows/columns. Only valid for certain style names (element-level styles within questions).

### Rule 27.6: Style variables via `arg:XXX` attribute
Custom style variables can be declared and referenced:
```xml
<style name="el.text" arg:before="$" mode="before">$(before)</style>
```
Variables are referenced as `$(var)` inside the style. When `copy`ing a style, supply new `arg:` values to override.

### Rule 27.7: `[rel file.jpg]` resolves relative to the survey directory
Official shortcut for static file references. Inserts a link relative to the current survey and routes through a caching proxy. The `[rel]` pipe works in `<style>` blocks and standard question text.
**Supplements:** Rule 19.2 (may not work inside `<html>` CDATA due to variable substitution)

### Rule 27.8: `${python code}` embeds Python expressions in style blocks
Style blocks support inline Python via `${expression}` syntax. Common uses:
- `${q3.r5.val}` — display a question value
- `${p.pipe}` — display a persistent variable
- `${v2_insertStyle('stylename')}` — insert another style block
This is separate from `<exec>` Python (Rule 20) and only works inside `<style>` blocks.

### Rule 27.9: `el.radio` renders `value="$(value)"` — confirming row value importance
The official `el.radio` template:
```html
<input type="radio" name="$(name)" value="$(value)" id=$(id) class="input radio" />
```
The `$(value)` comes from the `value` attribute on the `<row>` or `<col>` element. This confirms Rule 8.3: always set explicit `value=` attributes on rows.
**Confirms:** Rule 8.3

### Rule 27.10: `el.checkbox` always renders `value="1"` — row identity is in the `name`
The official `el.checkbox` template:
```html
<input type="checkbox" name="$(name)" id="$(id)" value="1" class="input checkbox" />
```
Unlike radios, checkboxes always have `value="1"`. The row is identified by the `name` attribute. This means:
- `input[value="r3"]` will NEVER find a checkbox
- Match by `name` attribute containing the row identifier
**Confirms:** Rule 12.1

### Rule 27.11: The `<survey>` tag supports `ss:customCSS` and `ss:customJS` for static files
**Per official Forsta docs**, for loading CSS/JS from the survey's `/static` directory:
```xml
<survey ss:customCSS="customScript" ss:customJS="customScript">
```
**IMPORTANT:** Specify filenames **WITHOUT file extensions** — Decipher appends `.css`/`.js` automatically. Using `ss:customJS="script.js"` would look for `script.js.js`.

For multiple files or full paths (including external), use `ss:includeCSS` / `ss:includeJS` (comma-delimited, WITH extensions):
```xml
<survey ss:includeJS="/survey/selfserve/9d3/proj1234/script1.js, proj1234/script2.js">
```
**Alternative to:** Rules 6.1, 7.1 — avoids CDATA bracket/template issues entirely
**Source:** Official Forsta "Including JavaScript in a Survey" and "Survey Style Attributes" docs

### Rule 27.12: `setup` attribute boilerplate values
Per official docs, `setup` accepts: `time`, `quota`, `term`, `decLang` (comma-separated).
- `term`: enables termination logic
- `quota`: enables quota-based routing
- `decLang`: enables language detection
- `time`: enables timing capture
**Confirms:** Rule 22.3

### Rule 27.13: `delphi="1"` enables advanced features and changes defaults
With `delphi="1"`:
- `persistentExit` is ON by default
- `autoRecover` is ON by default
- `capturePreciseTime` is ON by default
- `trackVars` is ON by default
- Data encryption requires AWS database with encryption enabled
- `allowDupe` is NOT usable
- `sql` storage is NOT usable

### Rule 27.14: `button.continue` has a known, stable ID
The official template always renders the Continue button as:
```html
<input type="submit" name="continue" id="btn_continue" class="button continue" />
```
This means `document.getElementById('btn_continue')` is the most reliable selector.
**Supplements:** Rule 15.4

### Rule 27.15: `question.after` with `wrap="ready"` is the recommended way to add per-question JS
```xml
<style name="question.after" with="Q1" wrap="ready"><![CDATA[
    $("#question_Q1").doSomething();
]]></style>
```
This avoids all `<html>` CDATA bracket issues (Rule 4.1) and `<script>` tag issues (Rule 7.3).
**Supplements:** Rules 7.1, 7.3, 24.1

### Rule 27.16: FIR (Form Image Replacement) — replaces browser form inputs with SVG
**Per official Forsta docs**, `fir="on"` replaces standard radio/checkbox browser inputs with scalable SVG graphics. Key behaviors:
- **Only radio and checkbox** inputs are replaced — text, textarea, select are unaffected
- **Underlying `<input>` elements remain in the DOM** — just visually hidden behind SVG
- **FIR can be toggled per-question** with `fir="off"` to disable for specific questions
- **compat 133+**: FIR allows radio DE-selection (click selected radio to uncheck). Add `$(".cell").addClass("no-uncheck")` via `respview.client.js` to disable this.
- **FIR styles**: `rounded` (default), `square`, `scale`, `fontawesome`/`fa`
- **Font Awesome icons** (compat 126+): Use `firStyle="fa"` with `firRadio`, `firRadioSelected`, `firCheckbox`, `firCheckboxSelected` attributes or equivalent themevars

**Impact on custom JS sync:**
- Native inputs still exist → custom JS can still target them
- SVG state changes are driven by native input events → dispatching proper events (Rule 11.3) keeps FIR visuals in sync
- If FIR is ON and custom JS changes `.checked` without events, the SVG graphic won't update

**FIR themevars** (cleaner than custom CSS for form styling):
```xml
<themevars>
  <themevar name="fir-border">#c7c7c7</themevar>
  <themevar name="fir-inner">#FFFFFF</themevar>
  <themevar name="fir-inner-hover">#8DDCDC</themevar>
  <themevar name="fir-inner-selected">#1CBAB9</themevar>
</themevars>
```
**Supplements:** Rules 11.2, 17.2, 24.2
**Source:** Official Forsta "Modifying Form Buttons" documentation

### Rule 27.17: `where="execute"` is valid on `<radio>` and `<checkbox>` — confirmed
The official Exec Tag docs show `where="execute"` as the standard pattern for hidden computed questions:
```xml
<radio label="vAge" where="execute">
  <exec>
  for eachRow in vAge.rows:
      if Q1.check(eachRow.o.alt):
          vAge.val = eachRow.index
          break
  </exec>
  <title>Age Group (Hidden)</title>
  <row label="r1" alt="1-17">1-17</row>
</radio>
```
Key API patterns from the docs:
- `question.val` — get/set question value
- `question.rows` — iterate over rows
- `eachRow.index` — get 1-based row index
- `eachRow.o.alt` — get row's `alt` attribute value
- `question.check(range)` — check if value is in range string (e.g., `"18-24"`)
- Nested `<exec>` inside `where="execute"` questions is the official pattern
**Confirms:** Rule 8.1 correction, Rule 20.5

### Rule 27.18: `<exec when="init">` supports `File()` and `Database()` for data loading
Per official docs, `when="init"` is for initializing static data structures:
```xml
<exec when="init">
myDatabase = File("dbfile.dat", "source")
badZipCodes = ["93611", "93720", "90210"]
</exec>
```
- `File("filename.dat", "key_column")` — loads tab-delimited file
- `Database("filename.txt")` — loads a validation database
- Variables declared in `when="init"` are available survey-wide
- **CANNOT** access question data, participant info, or extra variables
**Supplements:** Rules 20.2, 23.1

### Rule 27.19: `jsexport()` returns a JSON object of question properties in `question.after` styles
**Per official Forsta docs**, inside a `question.after` style block, `${jsexport()}` (Python interpolation) returns a JavaScript JSON object with the question's properties:
```xml
<style name="question.after" wrap="ready"><![CDATA[
    var qn = ${jsexport()};
    console.log(qn); // full question object: labels, rows, cols, values, etc.
]]></style>
```
This is useful for dynamically inspecting question structure at runtime without hardcoding row labels.
**Note:** Uses `${}` Python interpolation (Rule 3.1) — only works in style blocks, NOT in `<html>` CDATA.
**Source:** Official Forsta "Including JavaScript in a Survey" docs

### Rule 27.20: `Survey.setPersistent('client_name', value)` — JS-to-Python data bridge
**Per official Forsta docs**, `Survey.setPersistent(name, value)` saves data from JavaScript to a Python persistent variable:
```javascript
Survey.setPersistent("client_timing", elapsedTime);
```
Constraints:
- Variable name **MUST** start with `client_` prefix
- Value can be **any JSON object** (string, number, object, array)
- **Only ONE save per page** — multiple calls overwrite previous
- Retrieved in Python via `p.client_timing` (persistent variable)
- Requires a `<suspend/>` (page break) before the value is accessible in Python

Example from docs:
```xml
<html label="h1"><![CDATA[
<button onclick="Survey.setPersistent('client_data', {score: 42})">Save</button>
]]></html>
<suspend/>
<html label="h2">Score was: ${p.client_data}</html>
```
**Supplements:** Rule 20.6 (persistent variables)
**Source:** Official Forsta "Including JavaScript in a Survey" docs

### Rule 27.21: Complete list of `ss:` survey-level style attributes
**Per official Forsta "Survey Style Attributes" docs**, the following `ss:` attributes are valid on the `<survey>` tag:

| Attribute | Type | Description |
|-----------|------|-------------|
| `ss:customCSS` | string | CSS filename (no `.css` extension) from `/static` |
| `ss:customJS` | string | JS filename (no `.js` extension) from `/static` |
| `ss:includeCSS` | string | Comma-separated CSS file paths (with extensions) |
| `ss:includeJS` | string | Comma-separated JS file paths (with extensions) |
| `ss:enableNavigation` | bool | Add Back button |
| `ss:hideProgressBar` | bool | Hide progress bar |
| `ss:disableBackButton` | bool | Disable browser back button |
| `ss:disableOfflineDetection` | bool | Disable mobile connectivity warning |
| `ss:logoFile` | string | Logo image path |
| `ss:logoPosition` | string | Logo position |
| `ss:logoAlt` | string | Logo alt text (compat 133+) |
| `ss:colorScheme` | string | Survey color scheme |
| `ss:listDisplay` | bool | Display 1-column questions as lists vs tables |
| `ss:questionClassNames` | string | CSS classes on question container |
| `ss:rowClassNames` | string | CSS classes on row `<td>` elements |
| `ss:colClassNames` | string | CSS classes on col `<td>` elements |
| `ss:groupClassNames` | string | CSS classes on group `<td>` elements |
| `ss:choiceClassNames` | string | CSS classes on select `<option>` elements |
| `ss:commentClassNames` | string | CSS classes on comment elements |
| `ss:colWidth` | string | Column width |
| `ss:colLegendHeight` | string | Column legend height |
| `ss:legendColWidth` | string | Left/right legend width |
| `surveyDisplay` | string | Layout: `"auto"`, `"mobile"`, `"desktop"` |
| `html:showNumber` | bool | Show question numbers |
| `cs:preText` / `ss:preText` | string | Text before text/number inputs |
| `cs:postText` / `ss:postText` | string | Text after text/number inputs |

**Note:** `ss:rowClassNames`, `ss:colClassNames`, etc. can also be applied per-question, not just globally.
**Source:** Official Forsta "Survey Style Attributes" docs
