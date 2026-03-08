#!/usr/bin/env python3
"""
build_nm_section.py — Generate New Media survey XML from CSV database.

Reads NewMediaSurvey.csv, applies configurable score/eligibility filters,
and generates the Decipher XML blocks for all NM_SRC_T* and NM_INF_T*
questions. Output replaces the hardcoded topic blocks in Decipherxml.XML.

Usage:
    python build_nm_section.py                  # prints generated XML to stdout
    python build_nm_section.py --apply          # patches Decipherxml.XML in-place
    python build_nm_section.py --dry-run        # shows what would change (counts)

To update the survey after changing the CSV or filters:
    1. Edit FILTER_CONFIG below
    2. Run:  python build_nm_section.py --apply
    3. Upload the updated Decipherxml.XML to Decipher
"""

import csv
import html
import os
import re
import sys
from collections import defaultdict

# ================================================================
#  FILTER CONFIGURATION — Adjust these thresholds as needed
# ================================================================

# Global score minimums applied to ALL topics (0 = no filter).
FILTER_CONFIG = {
    'reach_score_min':          0,   # 0-3
    'uniqueness_score_min':     0,   # 0-3
    'recognition_score_min':    0,   # 0-3
    'scale_fit_score_min':      0,   # 0-3
    'strategic_priority_min':   0,   # 0+
    'require_field_eligible':           False,
    'require_field_eligible_relaxed':   False,
    'require_mainstream_flag':          None,  # None=ignore, 0=non-mainstream only, 1=mainstream only
}

# ================================================================
#  TOPIC CONFIGURATION
#  Maps NM_TOPICS row index → (CSV primary_topic, display title)
# ================================================================

TOPIC_CONFIG = [
    # (index, csv_primary_topic,                    display_title_for_question_text)
    (1,  'Political news and commentary',           'Political news and commentary'),
    (2,  'Health policy',                           'Health policy (insurance, drug prices, Medicare reform)'),
    (3,  'Medicare and senior health',              'Medicare and senior health issues'),
    (4,  'Natural and alternative health',          'Natural and alternative health'),
    (5,  'Nutrition and diet',                      'Nutrition and diet'),
    (6,  'Supplements and vitamins',                'Supplements and vitamins'),
    (7,  'Vaccines and immunization',               'Vaccines and immunization'),
    (8,  'Fitness and physical performance',        'Fitness and physical performance'),
    (9,  'Longevity and anti-aging',                'Longevity and anti-aging'),
    (10, 'Science and medical research',            'Science and medical research'),
    (11, 'Faith and values',                        'Faith and values'),
    (12, 'Worker and economic issues',              'Worker and economic issues'),
    (13, 'Health technology and innovation',        'Health technology and innovation'),
    (14, 'Environmental and climate health',        'Environmental and climate health'),
]

# ================================================================
#  PER-TOPIC FILTER RULES
#  Maps CSV primary_topic → additional filter overrides.
#  These are applied ON TOP of FILTER_CONFIG (overrides win).
#
#  Current logic:
#    Health Policy & Political News → field_eligible_relaxed = 1
#    Everything else               → mainstream_flag = 0
# ================================================================

HIGH_VOLUME_TOPICS = {
    'Health policy',
    'Political news and commentary',
}

TOPIC_FILTER_RULES = {}

# Build per-topic overrides from the rule above
for _t_idx, _csv_topic, _display in TOPIC_CONFIG:
    if _csv_topic in HIGH_VOLUME_TOPICS:
        TOPIC_FILTER_RULES[_csv_topic] = {
            'require_field_eligible_relaxed': True,
        }
    else:
        TOPIC_FILTER_RULES[_csv_topic] = {
            'require_mainstream_flag': 0,   # non-mainstream only
        }

# ================================================================
#  FILE PATHS
# ================================================================

CSV_PATH = os.path.join(os.path.dirname(__file__), 'NewMediaSurvey.csv')
XML_PATH = os.path.join(os.path.dirname(__file__), 'Decipherxml.XML')

# Markers in the XML for where to splice generated content
SPLICE_START_PATTERN = r'^<block label="nm_src_t1"'
SPLICE_END_TEXT = '</survey>'

# ================================================================
#  TRACK MAPPING: CSV track value → Decipher cond attribute
# ================================================================

TRACK_COND = {
    'GOP':  'NM_TRACK.r1',
    'DEM':  'NM_TRACK.r2',
    'BOTH': 'NM_TRACK.any',
}

# ================================================================
#  FILTER LOGIC
# ================================================================

def _merge_cfg(base, overrides):
    """Merge per-topic overrides on top of the base config."""
    if not overrides:
        return base
    merged = dict(base)
    merged.update(overrides)
    return merged


def passes_filter(row, cfg):
    """Return True if a CSV row passes all configured filters."""
    try:
        if cfg.get('reach_score_min') and int(row.get('reach_score', 0)) < cfg['reach_score_min']:
            return False
        if cfg.get('uniqueness_score_min') and int(row.get('uniqueness_score', 0)) < cfg['uniqueness_score_min']:
            return False
        if cfg.get('recognition_score_min') and int(row.get('recognition_score', 0)) < cfg['recognition_score_min']:
            return False
        if cfg.get('scale_fit_score_min') and int(row.get('scale_fit_score', 0)) < cfg['scale_fit_score_min']:
            return False
        if cfg.get('strategic_priority_min') and int(row.get('strategic_priority', 0)) < cfg['strategic_priority_min']:
            return False
        if cfg.get('require_field_eligible') and str(row.get('field_eligible', '0')).strip() != '1':
            return False
        if cfg.get('require_field_eligible_relaxed') and str(row.get('field_eligible_relaxed', '0')).strip() != '1':
            return False
        mf = cfg.get('require_mainstream_flag')
        if mf is not None and int(row.get('mainstream_flag', 0)) != int(mf):
            return False
    except (ValueError, TypeError):
        return False
    return True


def load_and_filter_csv(csv_path, cfg):
    """Read CSV, apply filters (with per-topic overrides), return sources and influencers grouped by topic."""
    sources = defaultdict(list)      # csv_topic -> [row, ...]
    influencers = defaultdict(list)   # csv_topic -> [row, ...]

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            topic = row.get('primary_topic', '').strip()
            # Merge global config with per-topic overrides
            effective_cfg = _merge_cfg(cfg, TOPIC_FILTER_RULES.get(topic))
            if not passes_filter(row, effective_cfg):
                continue
            rtype = row.get('record_type', '').strip().lower()
            if rtype in ('source', 'both'):
                sources[topic].append(row)
            if rtype in ('influencer', 'both'):
                influencers[topic].append(row)

    return sources, influencers


# ================================================================
#  XML ESCAPING
# ================================================================

def xesc(text):
    """Escape text for XML content."""
    return html.escape(text.strip(), quote=False)


# ================================================================
#  XML GENERATION — SOURCE (SWIPE CARD) BLOCKS
# ================================================================

def gen_src_rows(rows_list):
    """Generate <row> elements for a source rating question."""
    lines = []
    for i, row in enumerate(rows_list, 1):
        track = row.get('track', 'BOTH').strip().upper()
        cond = TRACK_COND.get(track, 'NM_TRACK.any')
        name = xesc(row.get('source_name', ''))
        lines.append(f'  <row label="r{i}" cond="{cond}">{name}</row>')
    return '\n'.join(lines)


def gen_src_block(tidx, csv_topic, display_title, rows_list):
    """Generate full XML for an NM_SRC_T{tidx} block."""
    q_label = f'NM_SRC_T{tidx}'
    oe_label = f'NM_SRC_T{tidx}_OE'
    block_label = f'nm_src_t{tidx}'
    badge_text = xesc(display_title)
    rows_xml = gen_src_rows(rows_list)

    return f'''<block label="{block_label}" cond="NM_TOPICS.r{tidx}">
<radio
  label="{q_label}"
  type="rating"
  values="order"
  averages="cols"
  shuffle="rows"
  optional="1"
  ss:questionClassNames="nm_hidden">
  <title>When was the last time you used this source for news and information on {xesc(display_title)}?</title>
{rows_xml}
  <col label="c1" value="1">Never heard of it</col>
  <col label="c2" value="2">Never used it</col>
  <col label="c3" value="3">Over a year ago</col>
  <col label="c4" value="4">Past year</col>
  <col label="c5" value="5">Past month</col>
  <col label="c6" value="6">Past week</col>

  <style mode="before" name="question.header"><![CDATA[
<div id="nm-root">
  <div class="nm-logo-bar"><img src="[rel PRISM_glyph.svg]" alt="PRISM"></div>
  <div id="nm-progress-wrap">
    <div class="nm-section-header">
      <span class="nm-section-title">NEW MEDIA</span>
      <span id="nm-progress-label">Sources</span>
    </div>
    <div id="nm-progress-track"><div id="nm-progress-fill"></div></div>
  </div>
  <div class="nm-card">
    <div class="nm-topic-badge">{badge_text}</div>
    <div class="nm-q-title">When was the last time you used this source?</div>
    <div class="nm-q-subtitle">One at a time &mdash; tap your answer and the next card appears automatically.</div>
    <div class="nm-swipe-wrap" id="nm-swipe-wrap">
      <div class="nm-swipe-counter" id="nm-swipe-counter"></div>
      <div class="nm-swipe-peek">
        <span class="nm-swipe-peek-left" id="nm-peek-left"></span>
        <span class="nm-swipe-peek-right" id="nm-peek-right"></span>
      </div>
      <div class="nm-swipe-card-area">
        <div class="nm-swipe-card" id="nm-card-text"></div>
      </div>
      <div class="nm-freq-btns" id="nm-freq-btns">
        <button type="button" class="nm-freq-btn" data-col="c1" data-val="1">Never heard<br>of it</button>
        <button type="button" class="nm-freq-btn" data-col="c2" data-val="2">Never<br>used it</button>
        <button type="button" class="nm-freq-btn" data-col="c3" data-val="3">Over a<br>year ago</button>
        <button type="button" class="nm-freq-btn" data-col="c4" data-val="4">Past<br>year</button>
        <button type="button" class="nm-freq-btn" data-col="c5" data-val="5">Past<br>month</button>
        <button type="button" class="nm-freq-btn" data-col="c6" data-val="6">Past<br>week</button>
      </div>
      <div class="nm-swipe-dots" id="nm-dots"></div>
    </div>
    <div class="nm-oe-wrap" id="nm-oe-wrap" style="display:none">
      <div class="nm-oe-title">Which publication or site should we have asked about?</div>
      <input type="text" class="nm-oe-input" id="nm-oe-input" placeholder="Type a name&hellip;">
      <button type="button" class="nm-oe-notsure" id="nm-oe-notsure">Not Sure</button>
    </div>
  </div>
  <div class="nm-continue-wrap">
    <div class="nm-error-prompt" id="nm-error">Please answer before continuing.</div>
    <button type="button" class="nm-continue-btn" id="nm-continue" disabled>CONTINUE &#8250;</button>
  </div>
  <div class="nm-footer">Your responses are held strictly confidential.
    See our <a href="#">Privacy Policy</a>
    and commitment to research ethics and integrity.</div>
</div>
]]></style>

  <style mode="after" name="question.footer"><![CDATA[
<script>
{_render_src_js(q_label, oe_label)}
</script>
]]></style>
</radio>

<text
  label="{oe_label}"
  optional="1"
  size="100"
  ss:questionClassNames="nm_hidden">
  <title>Which publication or site should we have asked about?</title>
</text>

<suspend/>
</block>'''


# ================================================================
#  XML GENERATION — INFLUENCER (CHIP GRID) BLOCKS
# ================================================================

def gen_inf_rows(rows_list):
    """Generate <row> elements for an influencer checkbox question."""
    lines = []
    for i, row in enumerate(rows_list, 1):
        track = row.get('track', 'BOTH').strip().upper()
        cond = TRACK_COND.get(track, 'NM_TRACK.any')
        name = xesc(row.get('source_name', ''))
        lines.append(f'  <row label="r{i}" cond="{cond}">{name}</row>')
    lines.append('  <row label="r99" exclusive="1">None of these</row>')
    return '\n'.join(lines)


def gen_inf_block(tidx, csv_topic, display_title, rows_list):
    """Generate full XML for an NM_INF_T{tidx} block."""
    q_label = f'NM_INF_T{tidx}'
    oe_label = f'NM_INF_T{tidx}_OE'
    block_label = f'nm_inf_t{tidx}'
    badge_text = xesc(display_title)
    rows_xml = gen_inf_rows(rows_list)

    return f'''<block label="{block_label}" cond="NM_TOPICS.r{tidx}">
<checkbox
  label="{q_label}"
  atleast="0"
  shuffle="rows"
  optional="1"
  ss:questionClassNames="nm_hidden">
  <title>Which of the following voices or creators do you follow on {xesc(display_title)}?</title>
  <comment>Scan the list and tap on any that you know and follow, no matter how often.</comment>
{rows_xml}

  <style mode="before" name="question.header"><![CDATA[
<div id="nm-root">
  <div class="nm-logo-bar"><img src="[rel PRISM_glyph.svg]" alt="PRISM"></div>
  <div id="nm-progress-wrap">
    <div class="nm-section-header">
      <span class="nm-section-title">NEW MEDIA</span>
      <span id="nm-progress-label">Voices &amp;amp; Creators</span>
    </div>
    <div id="nm-progress-track"><div id="nm-progress-fill"></div></div>
  </div>
  <div class="nm-card">
    <div class="nm-topic-badge">{badge_text}</div>
    <div class="nm-q-title">Which of the following voices or creators do you follow?</div>
    <div class="nm-q-subtitle">Scan the list and tap on any that you know and follow, no matter how often.</div>
    <div class="nm-inf-grid" id="nm-inf-grid"></div>
    <button type="button" class="nm-none-btn" id="nm-inf-none">None of these</button>
    <div class="nm-oe-wrap" id="nm-inf-oe-wrap" style="margin-top:20px">
      <div class="nm-oe-title">Which voices or creators did we forget to include?</div>
      <input type="text" class="nm-oe-input" id="nm-inf-oe-input" placeholder="Type a name&hellip;">
      <button type="button" class="nm-oe-notsure" id="nm-inf-oe-notsure">Not Sure</button>
    </div>
  </div>
  <div class="nm-continue-wrap">
    <div class="nm-error-prompt" id="nm-error">Please answer before continuing.</div>
    <button type="button" class="nm-continue-btn" id="nm-continue" disabled>CONTINUE &#8250;</button>
  </div>
  <div class="nm-footer">Your responses are held strictly confidential.
    See our <a href="#">Privacy Policy</a>
    and commitment to research ethics and integrity.</div>
</div>
]]></style>

  <style mode="after" name="question.footer"><![CDATA[
<script>
{_render_inf_js(q_label, oe_label)}
</script>
]]></style>
</checkbox>

<text
  label="{oe_label}"
  optional="1"
  size="100"
  ss:questionClassNames="nm_hidden">
  <title>Which voices or creators did we forget to include?</title>
</text>

<suspend/>
</block>'''


# ================================================================
#  SHARED JS TEMPLATES
#  These are the same helper functions + IIFE for each question.
#  {q_label} and {oe_label} are substituted per question.
# ================================================================

# JS helper functions (shared across all NM questions, but must be
# repeated per page since Decipher renders each page independently).
# Uses __Q_LABEL__ and __OE_LABEL__ placeholders (simple .replace()).
JS_HELPERS = r"""
function findQ(q){
    var el = document.getElementById('q_'+q)
        || document.getElementById('question_'+q)
        || document.getElementById(q)
        || document.querySelector('[id$="_'+q+'"]');
    if(el && el.closest && !el.classList.contains('question')){
      var par = el.closest('.question');
      if(par) el = par;
    }
    return el;
}
function syncCheckbox(qLabel, rowLabel, checked){
    var box = findQ(qLabel);
    if(!box){ console.warn('[NM syncCB] '+qLabel+' NOT FOUND'); return; }
    var inp = null;
    inp = box.querySelector('input[type="checkbox"][value="'+rowLabel+'"]');
    if(!inp) inp = box.querySelector('input[type="checkbox"][name*="'+rowLabel+'"]');
    if(!inp){
      var m = rowLabel.match(/^r(\d+)$/);
      if(m){
        var idx = parseInt(m[1], 10);
        var allCB = box.querySelectorAll('input[type="checkbox"]');
        if(idx === 99){
          for(var k=0; k<allCB.length; k++){
            var nm = (allCB[k].name||'')+(allCB[k].className||'');
            if(nm.indexOf('noanswer')!==-1||nm.indexOf('exclusive')!==-1){inp=allCB[k]; break;}
          }
          if(!inp && allCB.length>0) inp = allCB[allCB.length-1];
        } else if(idx>0 && idx<=allCB.length){
          inp = allCB[idx-1];
        }
      }
    }
    if(!inp){
      var all2 = box.querySelectorAll('input');
      for(var j=0; j<all2.length; j++){
        if(all2[j].value===rowLabel||(all2[j].name&&all2[j].name.indexOf(rowLabel)!==-1)){inp=all2[j]; break;}
      }
    }
    if(inp){
      inp.checked = checked;
      inp.click();
      inp.dispatchEvent(new Event('change', {bubbles:true}));
      try{ jQuery(inp).trigger('click').trigger('change'); }catch(e){}
    } else {
      console.warn('[NM syncCB] '+qLabel+'.'+rowLabel+' NO INPUT FOUND');
    }
}
function syncRating(qLabel, rowLabel, colVal){
    var box = findQ(qLabel);
    if(!box){ console.warn('[NM syncRating] '+qLabel+' NOT FOUND'); return; }
    var inp = null;
    inp = box.querySelector('input[type="radio"][name*="'+rowLabel+'"][value="'+colVal+'"]');
    if(!inp) inp = box.querySelector('input[name="'+qLabel+'_'+rowLabel+'"][value="'+colVal+'"]');
    if(!inp){
      var m = rowLabel.match(/^r(\d+)$/);
      if(m){
        var idx = parseInt(m[1], 10);
        var allRows = box.querySelectorAll('.fir-row, tr.row-elements, .row-elements');
        if(idx > 0 && idx <= allRows.length){
          inp = allRows[idx-1].querySelector('input[type="radio"][value="'+colVal+'"]');
        }
      }
    }
    if(!inp){
      var allR = box.querySelectorAll('input[type="radio"][value="'+colVal+'"]');
      for(var j=0; j<allR.length; j++){
        if(allR[j].name && allR[j].name.indexOf(rowLabel)!==-1){inp=allR[j]; break;}
      }
    }
    if(inp){
      inp.checked = true;
      inp.click();
      inp.dispatchEvent(new Event('change', {bubbles:true}));
      try{ jQuery(inp).trigger('click').trigger('change'); }catch(e){}
    } else {
      console.warn('[NM syncRating] '+qLabel+'.'+rowLabel+'='+colVal+' NO INPUT FOUND');
    }
}
function syncText(qLabel, val){
    var box = findQ(qLabel);
    if(!box){ console.warn('[NM syncText] '+qLabel+' NOT FOUND'); return; }
    var inp = box.querySelector('textarea') || box.querySelector('input[type="text"]');
    if(inp){
        inp.value = val;
        inp.dispatchEvent(new Event('change', {bubbles:true}));
        inp.dispatchEvent(new Event('input', {bubbles:true}));
        try{ jQuery(inp).trigger('change').trigger('input'); }catch(e){}
    }
}
function clickNext(){
    var nxt = document.querySelector('.nextPage, .button[type="submit"], input[type="submit"]');
    if(!nxt) nxt = document.querySelector('.button, input.button');
    if(nxt){
        nxt.setAttribute('style','display:block !important;visibility:hidden;position:absolute;left:-9999px;');
        nxt.click();
    } else {
        var form = document.querySelector('form');
        if(form) form.submit();
    }
}
function getRows(qLabel){
    var box = findQ(qLabel); if(!box){ console.warn('[NM getRows] '+qLabel+' NOT FOUND'); return []; }
    var rows = [], seen = {};
    var inputs = box.querySelectorAll('input[type="radio"], input[type="checkbox"]');
    for(var i=0; i<inputs.length; i++){
        var inp = inputs[i];
        var name = inp.name || '';
        var m = name.match(new RegExp('^'+qLabel+'_(r\\d+)'));
        if(!m) continue;
        var rLabel = m[1];
        if(seen[rLabel] || rLabel === 'r99') continue;
        seen[rLabel] = true;
        var rowEl = inp.closest('.fir-row') || inp.closest('tr') || inp.closest('.row-elements');
        if(!rowEl) rowEl = inp.parentNode;
        var textEl = rowEl ? (rowEl.querySelector('.fir-text') || rowEl.querySelector('.row-text') || rowEl.querySelector('label')) : null;
        var txt = textEl ? textEl.textContent.trim() : rLabel;
        if(txt === rLabel || txt.length < 2){
            var parent = inp.closest('.fir-row');
            if(parent){
                var fc = parent.querySelector('.fir-text-container, .fir-text, td:first-child, .row-label');
                if(fc) txt = fc.textContent.trim();
            }
        }
        rows.push({r: rLabel, name: txt});
    }
    return rows;
}
"""

SRC_JS_IIFE = r"""
(function(){
  var qLabel = '__Q_LABEL__';
  var oeLabel = '__OE_LABEL__';
  var items = getRows(qLabel);
  console.log('['+qLabel+'] getRows found '+items.length+' items');
  if(items.length === 0) return;
  var swipeIdx = 0, swipeAnswers = {}, oeNotSure = false;
  var cardText = document.getElementById('nm-card-text');
  var peekLeft = document.getElementById('nm-peek-left');
  var peekRight = document.getElementById('nm-peek-right');
  var freqBtns = document.getElementById('nm-freq-btns');
  var dotsEl = document.getElementById('nm-dots');
  var counterEl = document.getElementById('nm-swipe-counter');
  var oeWrap = document.getElementById('nm-oe-wrap');
  var oeInput = document.getElementById('nm-oe-input');
  var oeNotsure = document.getElementById('nm-oe-notsure');
  var continueBtn = document.getElementById('nm-continue');
  if(dotsEl){
    var dh = '';
    for(var i=0;i<items.length;i++) dh += '<div class="nm-swipe-dot'+(i===0?' nm-active':'')+'" data-idx="'+i+'"></div>';
    dotsEl.innerHTML = dh;
  }
  function updateSwipe(){
    if(!cardText) return;
    cardText.textContent = items[swipeIdx].name;
    if(counterEl) counterEl.textContent = (swipeIdx+1)+' of '+items.length;
    if(peekLeft) peekLeft.textContent = swipeIdx > 0 ? items[swipeIdx-1].name : '';
    if(peekRight) peekRight.textContent = swipeIdx < items.length-1 ? items[swipeIdx+1].name : '';
    if(freqBtns){
      var cur = swipeAnswers[items[swipeIdx].r];
      freqBtns.querySelectorAll('.nm-freq-btn').forEach(function(b){
        b.classList.remove('nm-flash');
        b.classList.toggle('nm-sel', b.getAttribute('data-col') === cur);
      });
    }
    if(dotsEl){
      dotsEl.querySelectorAll('.nm-swipe-dot').forEach(function(dot, i){
        dot.classList.toggle('nm-active', i === swipeIdx);
        dot.classList.toggle('nm-done', !!swipeAnswers[items[i].r]);
      });
    }
  }
  function updateContinue(){
    var allRated = items.every(function(item){ return swipeAnswers[item.r]; });
    continueBtn.disabled = !allRated;
    if(allRated && oeWrap) oeWrap.style.display = '';
  }
  if(freqBtns){
    freqBtns.querySelectorAll('.nm-freq-btn').forEach(function(btn){
      btn.addEventListener('click', function(){
        var col = btn.getAttribute('data-col');
        var val = btn.getAttribute('data-val');
        swipeAnswers[items[swipeIdx].r] = col;
        syncRating(qLabel, items[swipeIdx].r, val);
        freqBtns.querySelectorAll('.nm-freq-btn').forEach(function(b){ b.classList.remove('nm-sel','nm-flash'); });
        btn.classList.add('nm-flash');
        setTimeout(function(){
          btn.classList.remove('nm-flash');
          btn.classList.add('nm-sel');
          if(swipeIdx < items.length - 1){
            setTimeout(function(){ swipeIdx++; updateSwipe(); }, 150);
          } else {
            updateSwipe();
          }
          updateContinue();
        }, 400);
      });
    });
  }
  if(oeInput){
    oeInput.addEventListener('input', function(){
      syncText(oeLabel, oeInput.value);
      if(oeInput.value.length > 0 && oeNotSure){ oeNotSure = false; oeNotsure.classList.remove('nm-sel'); }
    });
  }
  if(oeNotsure){
    oeNotsure.addEventListener('click', function(){
      oeNotSure = !oeNotSure;
      oeNotsure.classList.toggle('nm-sel', oeNotSure);
      if(oeNotSure){ oeInput.value = 'Not Sure'; syncText(oeLabel, 'Not Sure'); }
      else { oeInput.value = ''; syncText(oeLabel, ''); }
    });
  }
  if(dotsEl){
    dotsEl.querySelectorAll('.nm-swipe-dot').forEach(function(dot){
      dot.addEventListener('click', function(){
        var idx = parseInt(dot.getAttribute('data-idx'), 10);
        if(!isNaN(idx) && idx >= 0 && idx < items.length){ swipeIdx = idx; updateSwipe(); }
      });
    });
  }
  if(continueBtn){
    continueBtn.addEventListener('click', function(){
      if(continueBtn.disabled) return;
      console.log('['+qLabel+' SUBMIT] answers=', JSON.stringify(swipeAnswers));
      clickNext();
    });
  }
  updateSwipe();
  updateContinue();
})();
"""

INF_JS_IIFE = r"""
(function(){
  var qLabel = '__Q_LABEL__';
  var oeLabel = '__OE_LABEL__';
  var items = getRows(qLabel);
  console.log('['+qLabel+'] getRows found '+items.length+' items');
  if(items.length === 0) return;
  var checks = {}, noneActive = false, oeNotSure = false;
  var grid = document.getElementById('nm-inf-grid');
  var noneBtn = document.getElementById('nm-inf-none');
  var oeInput = document.getElementById('nm-inf-oe-input');
  var oeNotsure = document.getElementById('nm-inf-oe-notsure');
  var continueBtn = document.getElementById('nm-continue');
  if(grid){
    var ch = '';
    for(var i=0;i<items.length;i++) ch += '<div class="nm-inf-chip" data-row="'+items[i].r+'">'+items[i].name+'</div>';
    grid.innerHTML = ch;
    grid.querySelectorAll('.nm-inf-chip').forEach(function(chip){
      chip.addEventListener('click', function(){
        var r = chip.getAttribute('data-row');
        checks[r] = !checks[r];
        chip.classList.toggle('nm-sel', checks[r]);
        syncCheckbox(qLabel, r, checks[r]);
        if(checks[r] && noneActive){
          noneActive = false;
          noneBtn.classList.remove('nm-sel');
          syncCheckbox(qLabel, 'r99', false);
        }
      });
    });
  }
  if(noneBtn){
    noneBtn.addEventListener('click', function(){
      noneActive = !noneActive;
      noneBtn.classList.toggle('nm-sel', noneActive);
      syncCheckbox(qLabel, 'r99', noneActive);
      if(noneActive){
        Object.keys(checks).forEach(function(r){ checks[r] = false; });
        grid.querySelectorAll('.nm-inf-chip').forEach(function(c){ c.classList.remove('nm-sel'); });
        var box = findQ(qLabel);
        if(box) box.querySelectorAll('input[type="checkbox"]').forEach(function(cb){
          if(cb.name && cb.name.indexOf('r99') === -1){ cb.checked = false; try{jQuery(cb).trigger('change');}catch(e){} }
        });
      }
    });
  }
  if(oeInput){
    oeInput.addEventListener('input', function(){
      syncText(oeLabel, oeInput.value);
      if(oeInput.value.length > 0 && oeNotSure){ oeNotSure = false; oeNotsure.classList.remove('nm-sel'); }
    });
  }
  if(oeNotsure){
    oeNotsure.addEventListener('click', function(){
      oeNotSure = !oeNotSure;
      oeNotsure.classList.toggle('nm-sel', oeNotSure);
      if(oeNotSure){ oeInput.value = 'Not Sure'; syncText(oeLabel, 'Not Sure'); }
      else { oeInput.value = ''; syncText(oeLabel, ''); }
    });
  }
  continueBtn.disabled = false;
  if(continueBtn){
    continueBtn.addEventListener('click', function(){
      if(continueBtn.disabled) return;
      console.log('['+qLabel+' SUBMIT] checks=', JSON.stringify(checks), 'none=', noneActive);
      var anyChecked = Object.keys(checks).some(function(k){ return checks[k]; });
      if(!anyChecked && !noneActive) syncCheckbox(qLabel, 'r99', true);
      clickNext();
    });
  }
})();
"""


def _render_src_js(q_label, oe_label):
    """Render the source swipe-card JS with placeholders replaced."""
    return (JS_HELPERS + SRC_JS_IIFE).replace('__Q_LABEL__', q_label).replace('__OE_LABEL__', oe_label)


def _render_inf_js(q_label, oe_label):
    """Render the influencer chip-grid JS with placeholders replaced."""
    return (JS_HELPERS + INF_JS_IIFE).replace('__Q_LABEL__', q_label).replace('__OE_LABEL__', oe_label)


# ================================================================
#  MAIN GENERATION
# ================================================================

def generate_nm_blocks(csv_path, cfg):
    """Generate all NM topic blocks from the CSV."""
    sources, influencers = load_and_filter_csv(csv_path, cfg)
    blocks = []

    # Header comment with active filter summary
    active_global = [f'{k}={v}' for k, v in cfg.items() if v]
    global_str = ', '.join(active_global) if active_global else 'none'
    topic_rules = []
    for csv_topic, rule in TOPIC_FILTER_RULES.items():
        parts = ', '.join(f'{k}={v}' for k, v in rule.items())
        topic_rules.append(f'       {csv_topic}: {parts}')
    topic_str = '\n'.join(topic_rules) if topic_rules else '       none'

    blocks.append(f'''<note>NM TOPIC BLOCKS -- AUTO-GENERATED from NewMediaSurvey.csv via build_nm_section.py. Global filters: {global_str}. To regenerate: python build_nm_section.py --apply</note>
''')

    for tidx, csv_topic, display_title in TOPIC_CONFIG:
        topic_sources = sources.get(csv_topic, [])
        topic_influencers = influencers.get(csv_topic, [])

        # Always generate SRC block (even if empty — the block cond handles visibility)
        if topic_sources:
            blocks.append(gen_src_block(tidx, csv_topic, display_title, topic_sources))
            blocks.append('')

        # Generate INF block only if there are influencer records
        if topic_influencers:
            blocks.append(gen_inf_block(tidx, csv_topic, display_title, topic_influencers))
            blocks.append('')

    return '\n\n'.join(blocks)


def apply_to_xml(xml_path, generated_content):
    """Replace the NM topic blocks section in the XML file."""
    with open(xml_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find the splice start: first <block label="nm_src_t1"
    start_idx = None
    for i, line in enumerate(lines):
        if re.search(SPLICE_START_PATTERN, line.strip()):
            start_idx = i
            break

    if start_idx is None:
        print("ERROR: Could not find splice start marker in XML.", file=sys.stderr)
        sys.exit(1)

    # Find the splice end: </survey> tag
    end_idx = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == SPLICE_END_TEXT:
            end_idx = i
            break

    if end_idx is None:
        print("ERROR: Could not find </survey> tag in XML.", file=sys.stderr)
        sys.exit(1)

    # Build new file content
    before = lines[:start_idx]
    after = lines[end_idx:]  # includes </survey>

    new_content = ''.join(before) + generated_content + '\n\n\n' + ''.join(after)

    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    old_lines = end_idx - start_idx
    new_lines = generated_content.count('\n') + 1
    return old_lines, new_lines


def print_summary(csv_path, cfg):
    """Print a summary of what the filter produces."""
    sources, influencers = load_and_filter_csv(csv_path, cfg)

    print("=" * 60)
    print("  NEW MEDIA BUILD SUMMARY")
    print("=" * 60)
    print()
    print("  GLOBAL FILTER CONFIG:")
    for key, val in cfg.items():
        marker = " <<<" if val else ""
        print(f"    {key}: {val}{marker}")
    print()
    print("  PER-TOPIC RULES:")
    for tidx, csv_topic, display_title in TOPIC_CONFIG:
        rule = TOPIC_FILTER_RULES.get(csv_topic)
        if rule:
            parts = ', '.join(f'{k}={v}' for k, v in rule.items())
            print(f"    {csv_topic}: {parts}")
    print()
    print(f"  {'TOPIC':<45} {'SRC':>5} {'INF':>5}  RULE")
    print(f"  {'-'*45} {'-'*5} {'-'*5}  {'-'*30}")

    total_src = 0
    total_inf = 0
    for tidx, csv_topic, display_title in TOPIC_CONFIG:
        ns = len(sources.get(csv_topic, []))
        ni = len(influencers.get(csv_topic, []))
        total_src += ns
        total_inf += ni
        rule = TOPIC_FILTER_RULES.get(csv_topic, {})
        rule_str = ', '.join(f'{k}={v}' for k, v in rule.items()) if rule else '(global only)'
        print(f"  {display_title:<45} {ns:>5} {ni:>5}  {rule_str}")

    print(f"  {'-'*45} {'-'*5} {'-'*5}")
    print(f"  {'TOTAL':<45} {total_src:>5} {total_inf:>5}")
    print()


def main():
    mode = 'stdout'
    if '--apply' in sys.argv:
        mode = 'apply'
    elif '--dry-run' in sys.argv:
        mode = 'dry-run'
    elif '--summary' in sys.argv:
        mode = 'summary'

    if mode == 'summary' or mode == 'dry-run':
        print_summary(CSV_PATH, FILTER_CONFIG)
        if mode == 'dry-run':
            sources, influencers = load_and_filter_csv(CSV_PATH, FILTER_CONFIG)
            total = sum(len(v) for v in sources.values()) + sum(len(v) for v in influencers.values())
            print(f"  Would generate XML for {total} total entries.")
            print(f"  Target file: {XML_PATH}")
        return

    generated = generate_nm_blocks(CSV_PATH, FILTER_CONFIG)

    if mode == 'apply':
        print_summary(CSV_PATH, FILTER_CONFIG)
        old_lines, new_lines = apply_to_xml(XML_PATH, generated)
        print(f"  APPLIED: Replaced {old_lines} hardcoded lines with {new_lines} generated lines.")
        print(f"  File updated: {XML_PATH}")
    else:
        # stdout mode — just print the generated XML
        print(generated)


if __name__ == '__main__':
    main()
