# DECIPHER.RULES.md

## Decipher XML Programming Rules for the PRISM Survey

> A catalogue of errors encountered and corrections applied during the development of the PRISM survey in Decipher (compat="146"), derived from the full commit history of `Decipherxml.XML`. These rules should be followed whenever generating or editing Decipher survey XML.

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
11. [Native Input Interop (setRadio)](#11-native-input-interop-setradio)
12. [Samplesources & Exit Pages](#12-samplesources--exit-pages)
13. [Theme References](#13-theme-references)
14. [CSS Content Restrictions](#14-css-content-restrictions)
15. [DOM Element IDs](#15-dom-element-ids)

---

## 1. XML Structure & Parsing

### Rule 1.1: One `<?xml?>` declaration only
**Error:** Duplicate `<?xml version="1.0"?>` declaration embedded inside the `<survey>` body caused a fatal WKDFJ save error.
**Fix:** Ensure only a single `<?xml?>` declaration exists at line 1 of the file. Never duplicate it inside the document body.
**Commit:** `a77c375` — *Fix fatal XML errors in Decipherxml.XML causing WKDFJ save error*

### Rule 1.2: Quote all attribute values
**Error:** Unquoted `style` attributes in `onerror` handlers caused XML parser failures.
**Fix:** Every attribute value must be enclosed in double quotes. Example: `style="display:none"`, not `style=display:none`.
**Commit:** `a77c375`

---

## 2. Namespaces & Attributes

### Rule 2.1: Do NOT declare `xmlns:builder`
**Error:** Declaring `xmlns:builder` in the `<survey>` tag caused a "redefined" validation error. Decipher provides this namespace automatically.
**Fix:** Omit `xmlns:builder` from the survey element. Only declare `xmlns:html` and `xmlns:ss`.
**Commit:** `1f77c24` — *Fix all Decipher validation errors*

### Rule 2.2: Do NOT use `builder:wizardCompleted`
**Error:** This attribute depends on the `xmlns:builder` namespace. Including it when the namespace is auto-provided (and cannot be redeclared) causes errors.
**Fix:** Remove `builder:wizardCompleted` from the survey element entirely.
**Commit:** `1f77c24`

### Rule 2.3: Valid namespace prefixes for compat="146"
The following are safe to use:
- `xmlns:html="http://www.w3.org/1999/xhtml"` — for `html:showNumber` etc.
- `xmlns:ss="http://www.decipherinc.com/ss"` — for `ss:disableBackButton`, `ss:enableNavigation`, `ss:hideProgressBar`

---

## 3. Character Encoding

### Rule 3.1: No raw non-ASCII characters in CDATA blocks
**Error:** 4-byte UTF-8 emoji characters (elephant U+1F418, donkey U+1FACF) and special dashes (non-breaking hyphen U+2011, em-dash U+2014) caused fatal server errors (XSVJV/DBNZJ) — likely a server-side storage/encoding crash.
**Fix:** Replace ALL non-ASCII characters with HTML numeric entities:
- `&#x1F418;` instead of 🐘
- `&#x2014;` instead of —
- `&#x2011;` instead of ‑

This applies to all content inside CDATA blocks. HTML entities render correctly because CDATA content becomes HTML output.
**Commit:** `5979b51` — *Replace all non-ASCII/emoji chars with HTML entities in CDATA*

### Rule 3.2: Use `&#x2026;` for ellipsis
**Error:** Raw Unicode ellipsis (…) caused XML parser safety warnings.
**Fix:** Replace `…` with `&#x2026;` in all text content.
**Commit:** `a77c375`

---

## 4. Square Brackets & Variable Substitution

### Rule 4.1: NEVER use square brackets in `<html>` CDATA content
**Error:** Decipher's `<html>` element runs `replaceVariables()` on its CDATA content, interpreting anything in square brackets `[...]` as a variable pipe reference.
- `pattern="[0-9]*"` → "Variable 0-9 not set" error
- `input[type="submit"]` in CSS → variable substitution crash
- `[rel PRISM_glyph.svg]` → may not resolve inside `<html>` CDATA

**Fix:** Move CSS/JS out of `<html>` elements into proper `<style name="respview.client.css">` and `<style name="respview.client.js">` blocks (see Rules 6 and 7).
**Commits:** `00bd236`, `9d15559`, `33796eb`

### Rule 4.2: Avoid `pattern` attributes with bracket syntax
**Error:** `pattern="[0-9]*"` on `<number>` or `<text>` elements causes Decipher to interpret `[0-9]` as a variable reference.
**Fix:** Remove `pattern` attributes. Use `type="tel"` and `inputmode="numeric"` for numeric input validation instead.
**Commit:** `00bd236` — *Remove pattern=[0-9]* attributes*

### Rule 4.3: Replace bracket CSS selectors if inside `<html>` elements
**Error:** `input[type="submit"]` CSS selector triggered variable substitution inside `<html>` CDATA.
**Fix:** Use class selectors instead (e.g., `.button` instead of `input[type="submit"]`). Or better: move CSS to `respview.client.css` where brackets are safe.
**Commit:** `9d15559` — *Add full CSS back, replace input[type=submit] with .button selector*

---

## 5. CDATA Blocks & Tag-Name Collisions

### Rule 5.1: Do NOT wrap CSS/JS in a `<style>` element at the survey level
**Error:** Decipher's server performs text-level matching of `</style>`. When CSS content inside a CDATA block contains `</style>` (the inner closing tag), the server prematurely terminates the outer `<style>` element, corrupting the XML parse.
**Fix:** Use `<html label="..." where="survey">` for inline content that contains `</style>` or `</script>` tags. Better yet, use the dedicated `<style name="respview.client.css">` block.
**Commit:** `1eaef3c` — *Change outer \<style\> to \<html\> to fix CDATA tag-name collision*

---

## 6. CSS Inclusion (respview.client.css)

### Rule 6.1: Use `<style name="respview.client.css">` for all CSS
**Correct structure:**
```xml
<style name="respview.client.css" mode="after"><![CDATA[
<style>
/* your CSS here */
</style>
]]></style>
```
The CDATA content is injected **raw** into the HTML `<head>`. You MUST include the inner `<style>...</style>` tags — Decipher does NOT auto-wrap.
**Commit:** `52ee305` — *Fix CSS/JS style blocks to match Decipher docs exactly*

### Rule 6.2: Do NOT nest an extra `<style>` tag inside the CDATA beyond what's needed
**Error:** Having `<style type="text/css">` inside the CDATA (instead of just `<style>`) was treated as invalid CSS text, preventing all styles from loading.
**Fix:** Use a plain `<style>` tag inside the CDATA — no `type` attribute.
**Commit:** `6fa015b` — *Fix CSS not loading in Decipher: remove nested style tag from CDATA*

### Rule 6.3: `mode="after"` loads CSS after Decipher's default styles
Use `mode="after"` on the `<style>` element to ensure your custom CSS overrides Decipher defaults. This is the standard approach for custom-styled surveys.

---

## 7. JavaScript Inclusion (respview.client.js)

### Rule 7.1: Use `<style name="respview.client.js" wrap="ready">` for all JS
**Correct structure:**
```xml
<style name="respview.client.js" wrap="ready"><![CDATA[
// your JavaScript here — runs inside jQuery(document).ready()
]]></style>
```
The `wrap="ready"` attribute auto-wraps the content in `<script>` tags and a `jQuery(document).ready()` block. Do NOT manually add `<script>` tags or jQuery ready wrappers.
**Commit:** `52ee305`

### Rule 7.2: Do NOT put `<script>` tags inside `<html>` CDATA
**Error:** Inline `<script>` tags inside `<html>` CDATA content do not execute reliably in Decipher and are subject to variable substitution (Rule 4.1).
**Fix:** Move all JavaScript to `<style name="respview.client.js" wrap="ready">`.
**Commit:** `b46ebc2` — *Move JS from inline \<script\> to respview.client.js style block*

### Rule 7.3: Use jQuery, not vanilla JS
Decipher bundles jQuery. The standard pattern is `jQuery(document).ready()`. When using `wrap="ready"`, jQuery is available as `$` or `jQuery`. Prefer jQuery selectors for DOM manipulation.
**Commit:** `b46ebc2`

---

## 8. Question Elements & Validation

### Rule 8.1: Use `cond="0"` for hidden question variables
**Error:** Using `where="execute"` on a `<text>` question element caused a fatal server error (XSVJV). The `where="execute"` attribute is only valid on `<html>` elements, not on question elements.
**Fix:** Use `cond="0"` to create a hidden/never-shown question variable:
```xml
<text label="vscreenout" cond="0" size="10">
  <title>Hidden screenout variable</title>
</text>
```
**Commits:** `1653e66`, `535df34` — *Fix vscreenout: use cond="0" instead of invalid where="execute"*

### Rule 8.2: Every variable referenced in `<exec>` must be declared
**Error:** `<exec>` blocks referenced `vscreenout.val` but the variable was never declared as a question element.
**Fix:** Declare any variable used in `<exec>` blocks as a question element (e.g., `<text label="vscreenout" cond="0">`).
**Commit:** `1653e66` — *Declare vscreenout variable used in exec screening blocks*

### Rule 8.3: Add explicit `value` attributes to `<row>` elements
**Error:** Rows without explicit `value` attributes caused mismatches when JavaScript tried to programmatically set radio inputs by numeric value.
**Fix:** Always add explicit `value="N"` to every `<row>`:
```xml
<row label="r1" value="1">Democrat</row>
<row label="r2" value="2">Republican</row>
```
**Commit:** `a6d2017` — *Fix setRadio to match Decipher input value formats and add explicit row values*

---

## 9. Survey Flow & Page Breaks

### Rule 9.1: `<suspend/>` creates a page break — questions after it cannot reference questions before it without a server round-trip
**Error:** Removing the suspend between QS5 and QS5A/QS5B was necessary because the custom JS UI managed all three questions as a single interactive card. With a suspend between them, QS5A/QS5B were on a different page and the JS couldn't interact with QS5.
**Fix:** Group questions that share a single custom UI card on the same page (no `<suspend/>` between them).
**Commit:** `f7e55e2` — *Add missing JavaScript and fix page structure for custom survey UI*

### Rule 9.2: Add `<suspend/>` BEFORE any `<exec>` that references prior-page answers
**Error:** QS5A/QS5B `<exec>` blocks needed to reference QS5 values, which requires a suspend (server round-trip) after QS5.
**Fix:** Place `<suspend/>` after the question whose data is needed and before the `<exec>` that reads it. Balancing this with Rule 9.1 requires careful page architecture.
**Commit:** `1f77c24`

### Rule 9.3: Use `.nextPage` to trigger native Decipher form submission
Custom "CONTINUE" buttons should trigger the native Decipher submit mechanism:
```javascript
$('.nextPage').click();
```
This ensures Decipher's server-side validation, screening logic, and page-break processing all fire correctly.
**Commit:** `32725a7` — *Add CONTINUE button for suspend submit*

---

## 10. Screening & Termination Logic

### Rule 10.1: Use `<exec>` with `setMarker()` for screening
Standard screening pattern:
```xml
<exec>
if QS1.r2 or QS1.r99:
    setMarker('Screened-QS1')
</exec>
<term label="Term_QS1" cond="hasMarker('Screened-QS1')">Thank you for your time.</term>
```
The `<exec>` evaluates the condition and sets a marker; the `<term>` element reads the marker.

### Rule 10.2: Use `cond=` (not `code=`) on `<exit>` elements
**Error:** `<exit code="qualified">` is not valid Decipher syntax.
**Fix:** Use `<exit cond="qualified">`, `<exit cond="terminated">`, `<exit cond="overquota">`.
**Commit:** `1f77c24`

---

## 11. Native Input Interop (setRadio)

### Rule 11.1: Decipher radio input `value` formats vary — check all three
When programmatically setting radio inputs via custom JavaScript, the native `<input>` elements may use different value formats:
1. `input[value="N"]` — explicit numeric value (when `value="N"` is set on `<row>`)
2. `input[value="rN"]` — Decipher row-label format (`r1`, `r2`, `r99`)
3. Nth radio by DOM index — fallback if neither selector matches

**Fix:** Try all three strategies:
```javascript
function setRadio(questionId, idx) {
    var container = document.getElementById(questionId);
    var input = container.querySelector('input[value="' + idx + '"]')
             || container.querySelector('input[value="r' + idx + '"]');
    if (!input) {
        var radios = container.querySelectorAll('input[type="radio"]');
        input = radios[idx - 1];
    }
    if (input) { input.checked = true; input.dispatchEvent(new Event('change', {bubbles:true})); }
}
```
**Commit:** `a6d2017` — *Fix setRadio to match Decipher input value formats*

### Rule 11.2: Always dispatch a `change` event after programmatically setting inputs
Decipher's framework listens for change events to register answers. Simply setting `.checked = true` is not enough.

---

## 12. Samplesources & Exit Pages

### Rule 12.1: Include `<samplesources>` with standard exit pages
At compat="146", the `<samplesources>` block is required for proper respondent routing:
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
**Commit:** `76a2210` — *Remove dangling after="Flag_prism" ref and add samplesources section*

### Rule 12.2: Do NOT use `after="..."` referencing non-existent labels
**Error:** `after="Flag_prism"` on a `<style>` element referenced a label that didn't exist, potentially crashing server-side element resolution.
**Fix:** Remove `after=` attributes that point to undefined labels.
**Commit:** `76a2210`

---

## 13. Theme References

### Rule 13.1: Only reference themes that exist on the target instance
**Error:** `theme="frozen:user/116957/dpi_project_temp"` caused a "theme not found" validation error when the theme didn't exist on the Decipher instance.
**Fix:** Remove the `theme` attribute if the theme is not available. The survey will use the default theme.
**Commit:** `1f77c24`

---

## 14. CSS Content Restrictions

### Rule 14.1: No `@keyframes` in Decipher style blocks
**Error:** The `@` prefix inside Decipher `<style>` CDATA can be interpreted as a template directive (`@if`, `@for`, etc.), potentially crashing the template engine.
**Fix:** Replace `@keyframes` animations with CSS `transition` properties instead.
**Commit:** `8411c7a` — *Fix multiple Decipher compatibility issues*

### Rule 14.2: Avoid CSS custom properties (`var()`)
**Error:** CSS `var()` custom properties were flagged as potential crash triggers during binary-search debugging.
**Fix:** Use direct values instead of CSS custom properties. Hard-code colors and sizes rather than using `var(--color-brand)` etc.
**Commit:** `c632e09` — *Add back first half of CSS, remove var() CSS custom properties*

### Rule 14.3: Avoid `-webkit-` vendor prefixes
**Error:** `-webkit-tap-highlight-color` and similar vendor prefixes were identified as potential triggers during crash isolation.
**Fix:** Omit vendor-prefixed properties unless absolutely necessary for rendering.
**Commit:** `c632e09`

---

## 15. DOM Element IDs

### Rule 15.1: Decipher generates question div IDs as `question_LABEL`
**Error:** JavaScript and CSS used `#q_QS1` but the actual Decipher-generated ID was `#question_QS1`.
**Fix:** Use `#question_LABEL` (e.g., `#question_QS1`, `#question_QZIP`) for all CSS selectors and `getElementById()` calls targeting Decipher question containers.
**Commit:** `8411c7a` — *Fix multiple Decipher compatibility issues*

### Rule 15.2: The `[rel ...]` pipe may not work inside `<html>` CDATA
**Error:** `[rel PRISM_glyph.svg]` asset references may only resolve inside `<style>` blocks, not inside `<html>` CDATA.
**Fix:** Use inline content (emoji, Base64 data URIs) or absolute URLs instead of `[rel]` pipes in `<html>` CDATA.
**Commit:** `8411c7a`

---

## Error History Summary

| # | Error Code / Symptom | Root Cause | Rule | Commit |
|---|----------------------|------------|------|--------|
| 1 | WKDFJ save error | Duplicate `<?xml?>` declaration | 1.1 | `a77c375` |
| 2 | WKDFJ save error | Unquoted attribute values | 1.2 | `a77c375` |
| 3 | Validation error | Undeclared `vscreenout` variable | 8.2 | `1653e66` |
| 4 | XSVJV fatal server error | `where="execute"` on `<text>` element | 8.1 | `535df34` |
| 5 | XSVJV/DBNZJ fatal server error | Non-ASCII emoji in CDATA | 3.1 | `5979b51` |
| 6 | Server crash | Dangling `after="Flag_prism"` ref | 12.2 | `76a2210` |
| 7 | CDATA parse corruption | `</style>` tag-name collision in CDATA | 5.1 | `1eaef3c` |
| 8 | Save crashes (binary search) | CSS content crash — isolated via 7 bisect commits | 14.1–14.3 | `661c489`→`2f90af6` |
| 9 | Namespace "redefined" error | `xmlns:builder` declared manually | 2.1 | `1f77c24` |
| 10 | Theme not found error | Invalid `theme=` reference | 13.1 | `1f77c24` |
| 11 | Invalid `code=` on `<exit>` | Should be `cond=` | 10.2 | `1f77c24` |
| 12 | "Variable 0-9 not set" | `pattern="[0-9]*"` bracket substitution | 4.2 | `00bd236` |
| 13 | Variable substitution crash | `input[type="submit"]` CSS selector in `<html>` | 4.3 | `9d15559` |
| 14 | CSS not loading | Extra `<style type="text/css">` inside CDATA | 6.2 | `6fa015b` |
| 15 | Buttons/interactions not working | No JavaScript present; custom UI had zero JS | 7.1 | `f7e55e2` |
| 16 | JS not executing | `<script>` inside `<html>` CDATA | 7.2 | `b46ebc2` |
| 17 | CSS/JS not loading | Wrong style block structure vs. Decipher docs | 6.1, 7.1 | `52ee305` |
| 18 | @keyframes crash | `@` interpreted as template directive | 14.1 | `8411c7a` |
| 19 | CSS/JS targeting wrong IDs | `q_LABEL` instead of `question_LABEL` | 15.1 | `8411c7a` |
| 20 | Termination not firing | Native radio inputs not being set by custom JS | 11.1 | `a6d2017` |

---

## Debugging Methodology: Binary Search for CDATA Crashes

When a CDATA block causes unexplained crashes, the commit history documents an effective binary-search approach:

1. **Minimal test** (`661c489`): Strip to 3 lines of CSS to confirm the element itself works
2. **Add half** (`c632e09`): Add ~140 lines (first half) to find crash threshold
3. **Full CSS, no JS** (`063d634`): Test full CSS without JS to isolate domain
4. **Progressive removal** (`5db0197` → `f47d084`): Remove CSS sections one-by-one
5. **Restore baseline** (`2246abf` → `2f90af6`): Return to known-good state and rebuild

This bisection technique across 7 commits ultimately identified that the content itself (not the CDATA mechanism) was the trigger — specifically `@keyframes`, `var()`, and vendor prefixes.

---

## Quick Reference: Correct Decipher XML Skeleton

```xml
<?xml version="1.0" encoding="UTF-8"?>
<survey
  compat="146"
  delphi="1"
  state="testing"
  xmlns:html="http://www.w3.org/1999/xhtml"
  xmlns:ss="http://www.decipherinc.com/ss"
  ss:hideProgressBar="1"
  html:showNumber="0">

  <!-- Resource strings -->
  <res label="...">...</res>

  <!-- Sample sources with exit pages -->
  <samplesources default="0">
    <samplesource list="0">
      <title>Open Survey</title>
      <exit cond="qualified">...</exit>
      <exit cond="terminated">...</exit>
      <exit cond="overquota">...</exit>
    </samplesource>
  </samplesources>

  <!-- CSS: raw HTML injected into <head> -->
  <style name="respview.client.css" mode="after"><![CDATA[
  <style>
  /* CSS here — brackets are safe */
  </style>
  ]]></style>

  <!-- JavaScript: auto-wrapped in jQuery ready -->
  <style name="respview.client.js" wrap="ready"><![CDATA[
  // JS here — runs in jQuery(document).ready()
  ]]></style>

  <!-- Custom HTML (no brackets! no </style> or </script>!) -->
  <html label="survey_ui" where="survey"><![CDATA[
  <div id="sc-root">...</div>
  ]]></html>

  <!-- Questions -->
  <radio label="Q1">
    <title>Question text</title>
    <row label="r1" value="1">Option 1</row>
    <row label="r2" value="2">Option 2</row>
  </radio>

  <suspend/>

  <!-- Screening -->
  <exec>
  if Q1.r2:
      setMarker('Screened-Q1')
  </exec>
  <term label="Term_Q1" cond="hasMarker('Screened-Q1')">Thank you.</term>

</survey>
```
