'use strict';

// ── 焦點編輯器 ──────────────────────────────────────────────────────────────

function initFocusEditor(root) {
    const preview  = root.querySelector('.focus-preview-wrap');
    const img      = preview.querySelector('img');
    const dot      = root.querySelector('.focus-dot');
    const slider   = root.querySelector('.focus-scale-slider');
    const scaleVal = root.querySelector('.focus-scale-val');

    const ctx = root.closest('.inline-related') || root.closest('form') || document;

    function findInput(name) {
        return ctx.querySelector('[name$="-' + name + '"], [name="' + name + '"]');
    }
    const inputX = findInput('image_focus_x');
    const inputY = findInput('image_focus_y');
    const inputS = findInput('image_scale');

    let x     = parseFloat(root.dataset.x);
    let y     = parseFloat(root.dataset.y);
    let scale = parseFloat(root.dataset.scale);

    function apply() {
        img.style.objectPosition  = x + '% ' + y + '%';
        img.style.transformOrigin = x + '% ' + y + '%';
        img.style.transform       = 'scale(' + scale + ')';
        dot.style.left = x + '%';
        dot.style.top  = y + '%';
        scaleVal.textContent = scale.toFixed(1) + '×';
        slider.value = scale;
        if (inputX) inputX.value = x;
        if (inputY) inputY.value = y;
        if (inputS) inputS.value = scale;
    }

    apply();

    let dragging = false;

    function posFromEvent(e) {
        const src  = e.touches ? e.touches[0] : e;
        const rect = preview.getBoundingClientRect();
        return {
            x: Math.round(Math.max(0, Math.min(1, (src.clientX - rect.left) / rect.width))  * 100),
            y: Math.round(Math.max(0, Math.min(1, (src.clientY - rect.top)  / rect.height)) * 100),
        };
    }

    function startDrag(e) {
        e.preventDefault();
        dragging = true;
        preview.classList.add('dragging');
        const p = posFromEvent(e);
        x = p.x; y = p.y;
        apply();
    }

    function onDrag(e) {
        if (!dragging) return;
        e.preventDefault();
        const p = posFromEvent(e);
        x = p.x; y = p.y;
        apply();
    }

    function stopDrag() {
        dragging = false;
        preview.classList.remove('dragging');
    }

    preview.addEventListener('mousedown',  startDrag);
    preview.addEventListener('touchstart', startDrag, { passive: false });

    document.addEventListener('mousemove',  onDrag);
    document.addEventListener('touchmove',  onDrag, { passive: false });

    document.addEventListener('mouseup',   stopDrag);
    document.addEventListener('touchend',  stopDrag);

    preview.addEventListener('wheel', function (e) {
        e.preventDefault();
        scale = Math.round(
            Math.max(0.5, Math.min(4.0, scale - e.deltaY * 0.002)) * 20
        ) / 20;
        apply();
    }, { passive: false });

    slider.addEventListener('input', function () {
        scale = parseFloat(this.value);
        apply();
    });
}

// ── 角色 Inline 切換選單 ─────────────────────────────────────────────────────

function initCharInlineTabs() {
    const group = document.getElementById('characters-group');
    if (!group) return;

    function getLiveRows() {
        return Array.from(group.querySelectorAll('div[id]'))
            .filter(r => /^characters-\d+$/.test(r.id));
    }

    const rows = getLiveRows();
    if (rows.length === 0) return;

    // ── 建立選單列 ──────────────────────────────────────────────────────────
    const header = document.createElement('div');
    header.className = 'char-switcher';

    const switcherLabel = document.createElement('span');
    switcherLabel.className = 'char-switcher-label';
    switcherLabel.textContent = '角色：';

    const select = document.createElement('select');
    select.className = 'char-switcher-select';

    header.append(switcherLabel, select);

    // 插在第一個 row 之前
    rows[0].parentNode.insertBefore(header, rows[0]);

    // ── 工具函式 ────────────────────────────────────────────────────────────
    function getCharName(row) {
        const inp = row.querySelector('[name$="-name"]');
        return (inp && inp.value.trim()) || '（新角色）';
    }

    function showRow(idx) {
        rows.forEach((r, i) => { r.style.display = i === idx ? '' : 'none'; });
        select.value = idx;
    }

    // ── 為每個既有 row 建立 option ──────────────────────────────────────────
    rows.forEach(function (row, i) {
        // 隱藏原本 h3
        const h3 = row.querySelector('h3');
        if (h3) h3.style.display = 'none';

        // 建立 option
        const opt = document.createElement('option');
        opt.value = i;
        opt.textContent = getCharName(row);
        select.appendChild(opt);

        // 名稱輸入時同步 option 文字
        const nameInp = row.querySelector('[name$="-name"]');
        if (nameInp) {
            nameInp.addEventListener('input', function () {
                opt.textContent = nameInp.value.trim() || '（新角色）';
            });
        }

        // 隱藏 rows（除第一個）
        if (i > 0) row.style.display = 'none';

        // 焦點編輯器
        const editor = row.querySelector('.char-focus-editor');
        if (editor) initFocusEditor(editor);
    });

    // ── select 切換 ─────────────────────────────────────────────────────────
    select.addEventListener('change', function () {
        showRow(parseInt(this.value, 10));
    });

    // ── 監聽 Django 新增 inline row（Django 4.0+ 原生 CustomEvent） ─────────
    document.addEventListener('formset:added', function (e) {
        // Django 4+ : e.detail.inline / e.detail.formsetName
        // fallback  : e.target
        const detail = e.detail || {};
        const newRow = detail.inline || (e.target !== document ? e.target : null);
        if (!newRow || !newRow.id) return;
        if (!/^characters-\d+$/.test(newRow.id)) return;

        const idx = rows.length;
        rows.push(newRow);

        const h3 = newRow.querySelector('h3');
        if (h3) h3.style.display = 'none';

        const opt = document.createElement('option');
        opt.value = idx;
        opt.textContent = '（新角色）';
        select.appendChild(opt);

        const nameInp = newRow.querySelector('[name$="-name"]');
        if (nameInp) {
            nameInp.addEventListener('input', function () {
                opt.textContent = nameInp.value.trim() || '（新角色）';
            });
        }

        // 切到新增的那筆
        showRow(idx);

        const editor = newRow.querySelector('.char-focus-editor');
        if (editor) initFocusEditor(editor);
    });
}

// ── 入口 ────────────────────────────────────────────────────────────────────

function init() {
    document.querySelectorAll('.char-focus-editor').forEach(initFocusEditor);
    initCharInlineTabs();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
