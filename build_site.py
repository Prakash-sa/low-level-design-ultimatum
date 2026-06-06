#!/usr/bin/env python3
"""
GitHub Pages Static Site Generator
Converts markdown files to HTML with navigation
"""

import os
import re
import sys
from pathlib import Path
import markdown
import json
from datetime import datetime
from urllib.parse import quote

class SiteGenerator:
    def __init__(self, root_dir, output_dir="_site"):
        self.root_dir = Path(root_dir).resolve()
        out_dir = Path(output_dir)
        # Normalize output directory to an absolute path so filtering works reliably
        self.output_dir = out_dir if out_dir.is_absolute() else (self.root_dir / out_dir).resolve()
        self.site_structure = {}
        self.pages = []
        # Base path where the site will be hosted (GitHub Pages project URL)
        self.base_url = "/low-level-design-ultimatum/"
        self.allowed_sections = [
            "Introduction",
            "Design Pattern",
            "Examples",
            "Company Tagged",
        ]
        self.section_labels = {
            "Introduction": "📚 Introduction",
            "Design Pattern": "🏗️ Design Pattern",
            "Examples": "💼 Examples",
            "Company Tagged": "🏢 Company Tagged",
        }

    def is_hidden(self, path):
        """Check if any part of the path is hidden (starts with a dot)"""
        return any(part.startswith('.') for part in path.relative_to(self.root_dir).parts)
    
    def build_tree(self, path):
        """Recursively build nav tree for folders and supported files"""
        items = []
        
        try:
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except Exception as e:
            print(f"Error reading {path}: {e}")
            return items
        
        for entry in entries:
            if entry == self.output_dir or self.output_dir in entry.parents:
                continue
            if self.is_hidden(entry) or entry.name in ('__pycache__',):
                continue
            
            if entry.is_dir():
                rel = entry.relative_to(self.root_dir)
                url = f"{self.base_url}{quote(rel.as_posix(), safe='/')}/"
                items.append({
                    "name": entry.name,
                    "url": url,
                    "type": "folder",
                    "items": self.build_tree(entry)
                })
            elif entry.suffix in ('.md', '.py'):
                rel = entry.relative_to(self.root_dir).with_suffix('.html')
                url = f"{self.base_url}{quote(rel.as_posix(), safe='/')}"
                items.append({
                    "name": entry.stem,
                    "url": url,
                    "type": "file",
                    "items": []
                })
        
        return items
    
    def build_section_tree(self, name):
        """Build nav tree for an allowed top-level section"""
        section_path = self.root_dir / name
        if not section_path.exists():
            return None
        
        encoded_name = quote(name)
        return {
            "name": self.section_labels.get(name, name),
            "url": f"{self.base_url}{encoded_name}/",
            "type": "folder",
            "items": self.build_tree(section_path)
        }
        
    def ensure_output_dir(self):
        """Create output directory structure"""
        self.output_dir.mkdir(exist_ok=True)
        
    def get_breadcrumb(self, file_path):
        """Generate breadcrumb navigation"""
        rel_path = file_path.relative_to(self.root_dir)
        parts = rel_path.parts[:-1]  # Exclude filename
        
        breadcrumbs = [{"name": "Home", "url": self.base_url}]
        current_url = self.base_url
        
        for part in parts:
            encoded = quote(part)
            current_url += f"{encoded}/"
            breadcrumbs.append({"name": part, "url": current_url})
        
        return breadcrumbs
    
    def read_markdown(self, file_path):
        """Read markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return ""
    
    def convert_to_html(self, markdown_content):
        """Convert markdown to HTML"""
        # Pull out ```mermaid blocks before markdown/codehilite touches them,
        # so they render as diagrams (via Mermaid.js) instead of escaped code.
        mermaid_blocks = []

        def _stash(match):
            mermaid_blocks.append(match.group(1).strip())
            return f"\n\nMERMAIDBLOCK{len(mermaid_blocks) - 1}ENDMERMAID\n\n"

        markdown_content = re.sub(
            r"```mermaid\s*\n(.*?)```",
            _stash,
            markdown_content,
            flags=re.DOTALL,
        )

        html_content = markdown.markdown(
            markdown_content,
            extensions=['extra', 'codehilite', 'toc']
        )

        # Re-insert each diagram as a <pre class="mermaid"> that Mermaid.js renders.
        for i, block in enumerate(mermaid_blocks):
            escaped = (block.replace("&", "&amp;")
                            .replace("<", "&lt;")
                            .replace(">", "&gt;"))
            placeholder = f"<p>MERMAIDBLOCK{i}ENDMERMAID</p>"
            html_content = html_content.replace(
                placeholder, f'<pre class="mermaid">{escaped}</pre>'
            )

        return html_content
    
    def get_nav_items(self, current_path=None):
        """Generate navigation items from folder structure (recursive tree)"""
        nav = []
        for name in self.allowed_sections:
            section = self.build_section_tree(name)
            if section:
                nav.append(section)
        return nav
    
    def generate_html_wrapper(self, title, content, breadcrumbs, nav_items):
        """Generate complete HTML page"""
        nav_html = self.generate_nav_html(nav_items)
        breadcrumb_html = self.generate_breadcrumb_html(breadcrumbs)

        html = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Low-Level Design Ultimatum</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css">
    <script>
        // Prevent flash-of-wrong-theme
        (function(){{
            var t = localStorage.getItem('lldu_theme') || 'light';
            document.documentElement.setAttribute('data-theme', t);
        }})();
    </script>
    <style>
        /* ── CSS Variables ─────────────────────────────── */
        :root {{
            --bg-page:       #f5f7ff;
            --bg-content:    #ffffff;
            --bg-sidebar:    linear-gradient(160deg, #667eea 0%, #764ba2 100%);
            --bg-navbar:     #ffffff;
            --text-primary:  #1a1a2e;
            --text-muted:    #64748b;
            --text-sidebar:  rgba(255,255,255,0.9);
            --border:        #e2e8f0;
            --accent:        #667eea;
            --accent-dark:   #764ba2;
            --navbar-shadow: 0 2px 10px rgba(0,0,0,0.08);
            --sidebar-width: 280px;
            --topbar-height: 56px;
            --progress-color:#667eea;
        }}
        [data-theme="dark"] {{
            --bg-page:       #0f1117;
            --bg-content:    #1a1c2a;
            --bg-sidebar:    linear-gradient(160deg, #1e1a3d 0%, #2d1a4a 100%);
            --bg-navbar:     #161824;
            --text-primary:  #e2e8f0;
            --text-muted:    #94a3b8;
            --text-sidebar:  rgba(255,255,255,0.85);
            --border:        #2d3148;
            --accent:        #818cf8;
            --accent-dark:   #a78bfa;
            --navbar-shadow: 0 2px 10px rgba(0,0,0,0.5);
            --progress-color:#818cf8;
        }}

        /* ── Reset ─────────────────────────────────────── */
        *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: var(--text-primary);
            background: var(--bg-page);
            padding-top: var(--topbar-height);
            transition: background .3s, color .3s;
        }}

        /* ── Reading Progress Bar ──────────────────────── */
        #reading-progress {{
            position: fixed;
            top: 0; left: 0;
            height: 3px;
            width: 0%;
            background: var(--progress-color);
            z-index: 2000;
            transition: width .1s linear;
        }}

        /* ── Top Navbar ────────────────────────────────── */
        .top-navbar {{
            position: fixed;
            top: 0; left: 0; right: 0;
            height: var(--topbar-height);
            background: var(--bg-navbar);
            box-shadow: var(--navbar-shadow);
            display: flex;
            align-items: center;
            padding: 0 18px;
            gap: 10px;
            z-index: 1100;
            transition: background .3s;
        }}
        .top-navbar .brand {{
            font-weight: 800;
            font-size: 1.1em;
            color: var(--accent);
            text-decoration: none;
            white-space: nowrap;
        }}
        .top-navbar .home-link {{
            color: var(--text-muted);
            text-decoration: none;
            font-size: .88em;
            font-weight: 500;
            padding: 5px 10px;
            border-radius: 6px;
            transition: background .2s, color .2s;
        }}
        .top-navbar .home-link:hover {{
            background: rgba(102,126,234,0.1);
            color: var(--accent);
            text-decoration: none;
        }}
        .top-navbar .spacer {{ flex: 1; }}
        .top-navbar .icon-btn {{
            background: none;
            border: 1.5px solid var(--border);
            border-radius: 8px;
            width: 34px; height: 34px;
            cursor: pointer;
            display: flex; align-items: center; justify-content: center;
            font-size: .95em;
            color: var(--text-muted);
            text-decoration: none;
            transition: background .2s, border-color .2s, color .2s;
            flex-shrink: 0;
        }}
        .top-navbar .icon-btn:hover {{
            border-color: var(--accent);
            color: var(--accent);
            background: rgba(102,126,234,0.08);
            text-decoration: none;
        }}
        .hamburger {{
            display: none;
            background: none;
            border: 1.5px solid var(--border);
            border-radius: 6px;
            width: 34px; height: 34px;
            cursor: pointer;
            align-items: center; justify-content: center;
            font-size: 1.1em;
            color: var(--text-muted);
        }}
        @media (max-width: 768px) {{ .hamburger {{ display: flex; }} }}

        /* ── Layout ────────────────────────────────────── */
        .wrapper {{
            display: flex;
            min-height: calc(100vh - var(--topbar-height));
        }}
        .sidebar {{
            width: var(--sidebar-width);
            background: var(--bg-sidebar);
            color: var(--text-sidebar);
            padding: 20px 16px;
            overflow-y: auto;
            flex-shrink: 0;
            position: sticky;
            top: var(--topbar-height);
            height: calc(100vh - var(--topbar-height));
            transition: transform .3s ease;
            z-index: 900;
        }}
        .sidebar h2 {{
            font-size: 1.1em;
            margin-bottom: 16px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(255,255,255,0.25);
            color: white;
        }}

        /* ── Sidebar Nav ───────────────────────────────── */
        .sidebar ul {{ list-style: none; padding-left: 0; margin-left: 0; }}
        .sidebar li {{ margin: 4px 0; }}
        .nav-row {{ display: flex; align-items: center; gap: 6px; }}
        .nav-toggle {{
            width: 22px; height: 22px;
            border: 1px solid rgba(255,255,255,0.5);
            background: transparent;
            color: white;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            line-height: 1;
            display: inline-flex; align-items: center; justify-content: center;
            transition: background .2s;
            flex-shrink: 0;
        }}
        .nav-toggle:hover {{ background: rgba(255,255,255,0.2); }}
        .nav-folder[data-collapsed="true"] .nav-toggle::after {{ content: "▶"; }}
        .nav-folder[data-collapsed="false"] .nav-toggle::after {{ content: "▼"; }}
        .nav-folder[data-collapsed="true"] > .nav-children {{ display: none; }}
        .nav-folder > .nav-children {{ margin-top: 6px; }}
        .sidebar a {{
            display: block;
            color: var(--text-sidebar);
            text-decoration: none;
            padding: 7px 10px;
            border-radius: 5px;
            transition: all .2s;
            word-break: break-word;
            font-size: .92em;
        }}
        .sidebar a:hover {{
            background: rgba(255,255,255,0.18);
            padding-left: 14px;
            text-decoration: none;
        }}
        .nav-file > a {{ padding-left: 30px; }}
        .nav-folder > .nav-row > a {{ font-weight: 600; }}
        .nav-children {{
            margin-left: 12px;
            border-left: 1px solid rgba(255,255,255,0.2);
            padding-left: 8px;
        }}

        /* ── Main Content ──────────────────────────────── */
        main {{
            flex: 1;
            padding: 36px 48px;
            background: var(--bg-content);
            min-width: 0;
            transition: background .3s;
        }}

        /* ── Breadcrumbs ───────────────────────────────── */
        .breadcrumbs {{
            margin-bottom: 24px;
            padding-bottom: 14px;
            border-bottom: 1px solid var(--border);
            font-size: .88em;
            color: var(--text-muted);
        }}
        .breadcrumbs a {{ color: var(--accent); text-decoration: none; margin: 0 4px; }}
        .breadcrumbs a:hover {{ text-decoration: underline; }}
        .breadcrumbs span {{ color: var(--text-muted); margin: 0 4px; }}

        /* ── Typography ────────────────────────────────── */
        h1 {{ color: var(--accent); margin-bottom: 28px; font-size: 1.9em; line-height: 1.2; }}
        h2 {{
            color: var(--accent);
            margin-top: 40px; margin-bottom: 14px;
            padding-bottom: 8px;
            border-bottom: 2px solid var(--accent);
            font-size: 1.4em;
        }}
        h3 {{ color: var(--accent-dark); margin-top: 24px; margin-bottom: 10px; }}

        /* ── Inline code ───────────────────────────────── */
        code {{
            background: rgba(102,126,234,0.10);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
            font-size: .88em;
            color: var(--accent-dark);
        }}

        /* ── Code blocks (Prism) ───────────────────────── */
        .code-block-wrapper {{
            position: relative;
            margin: 18px 0;
        }}
        pre {{
            border-radius: 8px !important;
            overflow-x: auto;
            margin: 0 !important;
            font-size: .86em !important;
            line-height: 1.5 !important;
        }}
        pre code {{
            background: none !important;
            padding: 0 !important;
            color: inherit !important;
            font-size: inherit !important;
            border-radius: 0 !important;
        }}
        .copy-btn {{
            position: absolute;
            top: 10px; right: 10px;
            padding: 4px 10px;
            font-size: .75em;
            background: rgba(255,255,255,0.12);
            color: #ccc;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 5px;
            cursor: pointer;
            transition: background .2s, color .2s;
            font-family: inherit;
            z-index: 10;
        }}
        .copy-btn:hover {{ background: rgba(255,255,255,0.22); color: white; }}
        .copy-btn.copied {{ background: #22c55e; color: white; border-color: #22c55e; }}

        /* ── Blockquote, Table ─────────────────────────── */
        blockquote {{
            border-left: 4px solid var(--accent);
            padding: 10px 16px;
            margin: 16px 0;
            color: var(--text-muted);
            background: rgba(102,126,234,0.05);
            border-radius: 0 6px 6px 0;
        }}
        table {{ width: 100%; border-collapse: collapse; margin: 16px 0; font-size: .95em; }}
        table th {{
            background: rgba(102,126,234,0.10);
            color: var(--accent);
            padding: 10px 14px;
            text-align: left;
            border-bottom: 2px solid var(--accent);
            font-weight: 600;
        }}
        table td {{ padding: 10px 14px; border-bottom: 1px solid var(--border); color: var(--text-primary); }}
        table tr:hover td {{ background: rgba(102,126,234,0.04); }}

        a {{ color: var(--accent); text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}

        .content {{ max-width: 860px; }}
        .content p {{ margin-bottom: 14px; color: var(--text-primary); }}
        .content ul, .content ol {{ margin-left: 22px; margin-bottom: 14px; }}
        .content li {{ margin-bottom: 6px; color: var(--text-primary); }}

        /* ── Mobile sidebar ────────────────────────────── */
        .sidebar-overlay {{
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.45);
            z-index: 1040;
        }}
        .sidebar-overlay.active {{ display: block; }}

        @media (max-width: 768px) {{
            .sidebar {{
                position: fixed;
                left: 0;
                top: var(--topbar-height);
                height: calc(100vh - var(--topbar-height));
                transform: translateX(-100%);
                z-index: 1050;
                box-shadow: 4px 0 20px rgba(0,0,0,0.3);
            }}
            .sidebar.open {{ transform: translateX(0); }}
            main {{ padding: 20px 18px; }}
            h1 {{ font-size: 1.5em; }}
        }}
    </style>
</head>
<body>
    <div id="reading-progress"></div>

    <div class="top-navbar">
        <button class="hamburger" id="hamburger" aria-label="Toggle sidebar">☰</button>
        <a href="{self.base_url}" class="brand">🎯 LLD</a>
        <a href="{self.base_url}" class="home-link">🏠 Home</a>
        <div class="spacer"></div>
        <a href="https://github.com/Prakash-sa/low-level-design-ultimatum"
           target="_blank" rel="noopener" class="icon-btn" title="View on GitHub">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 .3a12 12 0 0 0-3.8 23.4c.6.1.8-.3.8-.6v-2c-3.3.7-4-1.6-4-1.6-.5-1.4-1.3-1.8-1.3-1.8-1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1 1.8 2.8 1.3 3.4 1 .1-.8.4-1.3.7-1.6-2.7-.3-5.5-1.3-5.5-5.9 0-1.3.5-2.4 1.2-3.2 0-.4-.5-1.6.2-3.2 0 0 1-.3 3.3 1.2a11.5 11.5 0 0 1 6 0C17 5.1 18 5.4 18 5.4c.7 1.6.2 2.8.1 3.2.8.8 1.2 1.9 1.2 3.2 0 4.6-2.8 5.6-5.5 5.9.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6A12 12 0 0 0 12 .3"/>
            </svg>
        </a>
        <button class="icon-btn" id="darkModeBtn" title="Toggle dark mode" aria-label="Toggle dark mode">🌙</button>
    </div>

    <div class="sidebar-overlay" id="sidebarOverlay"></div>

    <div class="wrapper">
        <nav class="sidebar" id="sidebar">
            <h2>🎯 LLD</h2>
            {nav_html}
        </nav>
        <main>
            <div class="breadcrumbs">
                {breadcrumb_html}
            </div>
            <div class="content">
                {content}
            </div>
            <footer style="margin-top:60px; padding-top:20px; border-top:1px solid var(--border);
                           color:var(--text-muted); text-align:center; font-size:.88em;">
                <p>Last updated: {datetime.now().strftime('%Y-%m-%d')}</p>
                <p><a href="https://github.com/Prakash-sa/low-level-design-ultimatum">View on GitHub ↗</a></p>
            </footer>
        </main>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-core.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
        var dark = document.documentElement.getAttribute('data-theme') === 'dark';
        mermaid.initialize({{ startOnLoad: true, theme: dark ? 'dark' : 'default' }});
    </script>
    <script>
    // 1. DARK MODE
    (function() {{
        var btn = document.getElementById('darkModeBtn');
        var html = document.documentElement;
        var KEY = 'lldu_theme';
        var apply = function(theme) {{
            html.setAttribute('data-theme', theme);
            btn.textContent = theme === 'dark' ? '☀️' : '🌙';
        }};
        apply(localStorage.getItem(KEY) || 'light');
        btn.addEventListener('click', function() {{
            var next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            apply(next);
            localStorage.setItem(KEY, next);
        }});
    }})();

    // 2. READING PROGRESS BAR
    (function() {{
        var bar = document.getElementById('reading-progress');
        window.addEventListener('scroll', function() {{
            var docH = document.documentElement.scrollHeight - window.innerHeight;
            bar.style.width = (docH > 0 ? (window.scrollY / docH) * 100 : 0) + '%';
        }}, {{ passive: true }});
    }})();

    // 3. COPY CODE BUTTONS
    (function() {{
        document.querySelectorAll('pre').forEach(function(pre) {{
            if (pre.classList.contains('mermaid')) return;  // diagrams, not code
            var wrapper = document.createElement('div');
            wrapper.className = 'code-block-wrapper';
            pre.parentNode.insertBefore(wrapper, pre);
            wrapper.appendChild(pre);

            var btn = document.createElement('button');
            btn.className = 'copy-btn';
            btn.textContent = 'Copy';
            wrapper.appendChild(btn);

            btn.addEventListener('click', function() {{
                var text = pre.innerText || pre.textContent || '';
                var done = function() {{
                    btn.textContent = 'Copied!';
                    btn.classList.add('copied');
                    setTimeout(function() {{
                        btn.textContent = 'Copy';
                        btn.classList.remove('copied');
                    }}, 2000);
                }};
                if (navigator.clipboard && navigator.clipboard.writeText) {{
                    navigator.clipboard.writeText(text).then(done).catch(function() {{
                        fallbackCopy(text); done();
                    }});
                }} else {{ fallbackCopy(text); done(); }}
            }});

            // Ensure Prism highlights as Python if no language class set
            var codeEl = pre.querySelector('code');
            if (codeEl && !codeEl.className.includes('language-')) {{
                codeEl.classList.add('language-python');
            }}
        }});

        function fallbackCopy(text) {{
            var ta = document.createElement('textarea');
            ta.value = text;
            ta.style.cssText = 'position:fixed;opacity:0;top:0;left:0';
            document.body.appendChild(ta);
            ta.select();
            try {{ document.execCommand('copy'); }} catch(e) {{}}
            document.body.removeChild(ta);
        }}

        if (window.Prism) Prism.highlightAll();
    }})();

    // 4. MOBILE SIDEBAR TOGGLE
    (function() {{
        var hamburger = document.getElementById('hamburger');
        var sidebar   = document.getElementById('sidebar');
        var overlay   = document.getElementById('sidebarOverlay');
        var openSidebar = function() {{
            sidebar.classList.add('open');
            overlay.classList.add('active');
            hamburger.textContent = '✕';
        }};
        var closeSidebar = function() {{
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
            hamburger.textContent = '☰';
        }};
        hamburger.addEventListener('click', function() {{
            sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
        }});
        overlay.addEventListener('click', closeSidebar);
    }})();

    // 5. SIDEBAR NAV COLLAPSE/EXPAND (preserved original logic)
    document.addEventListener('DOMContentLoaded', function() {{
        var toggles = document.querySelectorAll('.nav-toggle');
        var expandedKey = 'lldu_nav_expanded';

        var loadExpanded = function() {{
            try {{ return JSON.parse(localStorage.getItem(expandedKey)) || []; }}
            catch(e) {{ return []; }}
        }};
        var saveExpanded = function(paths) {{
            try {{ localStorage.setItem(expandedKey, JSON.stringify(paths)); }}
            catch(e) {{}}
        }};

        var expandedPaths = new Set(loadExpanded());

        var applyState = function(li) {{
            var path = li.getAttribute('data-path');
            var isExpanded = expandedPaths.has(path);
            li.setAttribute('data-collapsed', isExpanded ? 'false' : 'true');
            var btn = li.querySelector('.nav-toggle');
            if (btn) btn.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
        }};

        document.querySelectorAll('.nav-folder').forEach(applyState);

        toggles.forEach(function(btn) {{
            btn.addEventListener('click', function(event) {{
                event.preventDefault();
                var li = btn.closest('.nav-folder');
                var path = li.getAttribute('data-path');
                var collapsed = li.getAttribute('data-collapsed') === 'true';
                var newCollapsed = !collapsed;
                li.setAttribute('data-collapsed', newCollapsed ? 'true' : 'false');
                btn.setAttribute('aria-expanded', newCollapsed ? 'false' : 'true');
                if (newCollapsed) {{ expandedPaths.delete(path); }}
                else {{ expandedPaths.add(path); }}
                saveExpanded([...expandedPaths]);
            }});
            btn.addEventListener('keydown', function(event) {{
                if (event.key === 'Enter' || event.key === ' ') {{
                    event.preventDefault();
                    btn.click();
                }}
            }});
        }});
    }});
    </script>
</body>
</html>"""
        return html
    
    def generate_nav_html(self, nav_items):
        """Generate navigation HTML as nested tree"""
        def render(items):
            html = "<ul>"
            for item in items:
                item_class = "nav-folder" if item["type"] == "folder" else "nav-file"
                if item["type"] == "folder":
                    html += (
                        f'<li class="{item_class}" data-collapsed="true" data-path="{item["url"]}">'
                        f'<div class="nav-row">'
                        f'<button class="nav-toggle" aria-label="Toggle {item["name"]}" aria-expanded="false"></button>'
                        f'<a href="{item["url"]}">{item["name"]}</a>'
                        f'</div>'
                    )
                    html += f'<div class="nav-children">{render(item["items"])}</div>'
                    html += "</li>"
                else:
                    html += f'<li class="{item_class}"><a href="{item["url"]}">{item["name"]}</a></li>'
            html += "</ul>"
            return html
        
        return render(nav_items)
    
    def generate_breadcrumb_html(self, breadcrumbs):
        """Generate breadcrumb HTML"""
        html = ""
        for i, crumb in enumerate(breadcrumbs):
            if i > 0:
                html += ' <span>/</span> '
            html += f'<a href="{crumb["url"]}">{crumb["name"]}</a>'
        return html
    
    def process_directory_index(self, folder_path):
        """Generate index.html for directories"""
        output_path = self.output_dir / folder_path.relative_to(self.root_dir) / "index.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        items = []
        try:
            for item in sorted(folder_path.iterdir()):
                if self.is_hidden(item) or item.name == '__pycache__':
                    continue
                
                rel_path = item.relative_to(self.root_dir)
                
                if item.is_dir():
                    items.append({
                        "name": item.name,
                        "type": "folder",
                        "url": f"{self.base_url}{quote('/'.join(rel_path.parts), safe='/')}/"
                    })
                elif item.suffix == '.md':
                    items.append({
                        "name": item.stem,
                        "type": "file",
                        "url": f"{self.base_url}{quote('/'.join(rel_path.with_suffix('').parts), safe='/')}.html"
                    })
                elif item.suffix in ['.py']:
                    items.append({
                        "name": item.name,
                        "type": "code",
                        "url": f"{self.base_url}{quote('/'.join(rel_path.with_suffix('').parts), safe='/')}.html"
                    })
        except Exception as e:
            print(f"Error processing directory {folder_path}: {e}")
        
        # Generate HTML content
        content = f"<h1>{folder_path.name}</h1>\n"
        
        if items:
            content += '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px; margin-top: 20px;">\n'
            
            for item in items:
                icon = "📁" if item["type"] == "folder" else "📄" if item["type"] == "file" else "🐍"
                content += f"""<a href="{item['url']}" style="
                    display: block;
                    padding: 15px;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                    text-decoration: none;
                    color: #333;
                    transition: all 0.3s ease;
                " onmouseover="this.style.boxShadow='0 5px 15px rgba(0,0,0,0.1)'; this.style.borderColor='#667eea';" onmouseout="this.style.boxShadow='none'; this.style.borderColor='#e0e0e0';">
                    <div style="font-size: 1.5em; margin-bottom: 10px;">{icon}</div>
                    <div style="font-weight: 500;">{item['name']}</div>
                </a>
"""
            
            content += '</div>\n'
        else:
            content += '<p>No items in this directory.</p>\n'
        
        title = folder_path.name
        breadcrumbs = self.get_breadcrumb(folder_path)
        nav_items = self.get_nav_items()
        
        html = self.generate_html_wrapper(title, content, breadcrumbs, nav_items)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"Generated: {output_path}")
    
    def process_markdown_file(self, file_path):
        """Convert markdown file to HTML"""
        try:
            rel_path = file_path.relative_to(self.root_dir)
            output_path = self.output_dir / rel_path.with_suffix('.html')
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read and convert markdown
            markdown_content = self.read_markdown(file_path)
            html_content = self.convert_to_html(markdown_content)
            
            # Extract title from first heading or filename
            title = rel_path.stem
            
            # Generate breadcrumbs and nav
            breadcrumbs = self.get_breadcrumb(file_path)
            nav_items = self.get_nav_items(file_path)
            
            # Wrap in full HTML
            full_html = self.generate_html_wrapper(title, html_content, breadcrumbs, nav_items)
            
            # Write output
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_html)
            
            print(f"Generated: {output_path}")
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    def process_code_file(self, file_path):
        """Convert code file to HTML"""
        try:
            rel_path = file_path.relative_to(self.root_dir)
            output_path = self.output_dir / rel_path.with_suffix('.html')
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read code file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code_content = f.read()
            
            # Wrap in code block
            html_content = f'<pre><code>{code_content}</code></pre>'
            
            title = file_path.name
            breadcrumbs = self.get_breadcrumb(file_path)
            nav_items = self.get_nav_items()
            
            full_html = self.generate_html_wrapper(title, html_content, breadcrumbs, nav_items)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_html)
            
            print(f"Generated: {output_path}")
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    def generate(self):
        """Generate entire site"""
        print("Starting site generation...")
        self.ensure_output_dir()
        
        # Ensure .nojekyll is present so GitHub Pages serves all files
        nojekyll_src = self.root_dir / ".nojekyll"
        if nojekyll_src.exists():
            nojekyll_dst = self.output_dir / ".nojekyll"
            nojekyll_dst.write_text(nojekyll_src.read_text(encoding="utf-8"), encoding="utf-8")
        
        # Copy index.html
        index_src = self.root_dir / "index.html"
        if index_src.exists():
            index_dst = self.output_dir / "index.html"
            with open(index_src, 'r') as f:
                with open(index_dst, 'w') as out:
                    out.write(f.read())
            print(f"Copied: {index_dst}")
        
        # Process all markdown files
        for md_file in self.root_dir.rglob('*.md'):
            if self.output_dir in md_file.parents or self.is_hidden(md_file):
                continue
            self.process_markdown_file(md_file)
        
        # Process all Python files
        for py_file in self.root_dir.rglob('*.py'):
            if self.output_dir in py_file.parents or self.is_hidden(py_file):
                continue
            self.process_code_file(py_file)
        
        # Generate directory indexes
        for folder in self.root_dir.rglob('*'):
            if folder == self.output_dir or self.output_dir in folder.parents:
                continue
            if folder.is_dir() and not self.is_hidden(folder) and folder.name != '__pycache__':
                self.process_directory_index(folder)
        
        print("Site generation completed!")

if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    generator = SiteGenerator(root)
    generator.generate()
