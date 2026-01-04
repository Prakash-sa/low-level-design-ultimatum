#!/usr/bin/env python3
"""
GitHub Pages Static Site Generator
Converts markdown files to HTML with navigation
"""

import os
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
        html_content = markdown.markdown(
            markdown_content,
            extensions=['extra', 'codehilite', 'toc']
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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Low-Level Design Ultimatum</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}
        
        .wrapper {{
            display: flex;
            min-height: 100vh;
        }}
        
        nav {{
            width: 280px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            overflow-y: auto;
            box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
        }}
        
        nav h2 {{
            font-size: 1.2em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.3);
        }}
        
        nav ul {{
            list-style: none;
            padding-left: 0;
            margin-left: 0;
        }}
        
        nav li {{
            margin: 4px 0;
        }}
        
        .nav-row {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        
        .nav-toggle {{
            width: 22px;
            height: 22px;
            border: 1px solid rgba(255, 255, 255, 0.5);
            background: transparent;
            color: white;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            line-height: 1;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }}
        
        .nav-toggle:hover {{
            background: rgba(255, 255, 255, 0.2);
        }}
        
        .nav-folder[data-collapsed="true"] .nav-toggle::after {{
            content: "▶";
        }}
        
        .nav-folder[data-collapsed="false"] .nav-toggle::after {{
            content: "▼";
        }}
        
        .nav-folder[data-collapsed="true"] > .nav-children {{
            display: none;
        }}
        
        .nav-folder > .nav-children {{
            margin-top: 6px;
        }}
        
        nav a {{
            display: block;
            color: white;
            text-decoration: none;
            padding: 8px 10px;
            border-radius: 4px;
            transition: all 0.2s ease;
            word-break: break-word;
        }}
        
        nav a:hover {{
            background: rgba(255, 255, 255, 0.2);
            padding-left: 14px;
        }}
        
        .nav-folder > a {{
            font-weight: 600;
        }}
        
        .nav-children {{
            margin-left: 12px;
            border-left: 1px solid rgba(255, 255, 255, 0.2);
            padding-left: 8px;
        }}
        
        main {{
            flex: 1;
            padding: 40px;
            background: white;
        }}
        
        .breadcrumbs {{
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .breadcrumbs a {{
            color: #667eea;
            text-decoration: none;
            margin: 0 5px;
        }}
        
        .breadcrumbs a:hover {{
            text-decoration: underline;
        }}
        
        .breadcrumbs span {{
            color: #999;
            margin: 0 5px;
        }}
        
        h1 {{
            color: #667eea;
            margin-bottom: 30px;
            font-size: 2em;
        }}
        
        h2 {{
            color: #667eea;
            margin-top: 40px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        
        h3 {{
            color: #764ba2;
            margin-top: 25px;
            margin-bottom: 10px;
        }}
        
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            color: #d63384;
        }}
        
        pre {{
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 15px 0;
            line-height: 1.4;
        }}
        
        pre code {{
            background: none;
            color: inherit;
            padding: 0;
        }}
        
        blockquote {{
            border-left: 4px solid #667eea;
            padding-left: 15px;
            margin: 15px 0;
            color: #666;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        
        table th {{
            background: #f4f4f4;
            padding: 10px;
            text-align: left;
            border-bottom: 2px solid #ddd;
            font-weight: 600;
        }}
        
        table td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        
        a {{
            color: #667eea;
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        .content {{
            max-width: 900px;
        }}
        
        .content p {{
            margin-bottom: 15px;
        }}
        
        .content ul, .content ol {{
            margin-left: 20px;
            margin-bottom: 15px;
        }}
        
        .content li {{
            margin-bottom: 8px;
        }}
        
        @media (max-width: 768px) {{
            .wrapper {{
                flex-direction: column;
            }}
            
            nav {{
                width: 100%;
                max-height: 300px;
                border-bottom: 1px solid #ddd;
            }}
            
            main {{
                padding: 20px;
            }}
            
            h1 {{
                font-size: 1.5em;
            }}
        }}
    </style>
</head>
<body>
    <div class="wrapper">
        <nav>
            <h2>🎯 Navigation</h2>
            {nav_html}
        </nav>
        <main>
            <div class="breadcrumbs">
                {breadcrumb_html}
            </div>
            <div class="content">
                {content}
            </div>
            <footer style="margin-top: 60px; padding-top: 20px; border-top: 1px solid #e0e0e0; color: #999; text-align: center; font-size: 0.9em;">
                <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <p><a href="https://github.com/Prakash-sa/low-level-design-ultimatum" style="color: #667eea;">View on GitHub</a></p>
            </footer>
        </main>
    </div>
</body>
</html>
<script>
// Simple nav collapse/expand
document.addEventListener('DOMContentLoaded', () => {
    const toggles = document.querySelectorAll('.nav-toggle');
    toggles.forEach(btn => {
        btn.addEventListener('click', (event) => {
            event.preventDefault();
            const li = btn.closest('.nav-folder');
            const collapsed = li.getAttribute('data-collapsed') === 'true';
            li.setAttribute('data-collapsed', collapsed ? 'false' : 'true');
        });
    });
});
</script>"""
        return html
    
    def generate_nav_html(self, nav_items):
        """Generate navigation HTML as nested tree"""
        def render(items):
            html = "<ul>"
            for item in items:
                item_class = "nav-folder" if item["type"] == "folder" else "nav-file"
                if item["type"] == "folder":
                    html += (
                        f'<li class="{item_class}" data-collapsed="false">'
                        f'<div class="nav-row">'
                        f'<button class="nav-toggle" aria-label="Toggle {item["name"]}"></button>'
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
