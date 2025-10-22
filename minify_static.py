#!/usr/bin/env python3
"""
Script to minify CSS and JS files for the FetDate application
"""
import os
import re
import glob
from pathlib import Path


def minify_css(content):
    """Remove comments and whitespace from CSS"""
    # Remove comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    # Remove whitespace around special characters
    content = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', content)
    # Remove extra whitespace
    content = re.sub(r'\s+', ' ', content)
    # Remove whitespace after opening and before closing braces
    content = re.sub(r'\{\s+', '{', content)
    content = re.sub(r'\s+\}', '}', content)
    # Remove leading/trailing whitespace
    content = content.strip()
    return content


def minify_js(content):
    """Simple minification for JS - remove comments and whitespace"""
    # Remove single-line comments
    content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
    # Remove multi-line comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    # Remove extra whitespace
    content = re.sub(r'\s+', ' ', content)
    # Remove whitespace around operators
    content = re.sub(r'\s*([{}:;,>+~()=\[\]])\s*', r'\1', content)
    # Remove leading/trailing whitespace
    content = content.strip()
    return content


def process_static_files():
    """Process and minify CSS and JS files"""
    static_dir = Path('static')
    
    # Process CSS files
    css_files = list(static_dir.rglob('*.css'))
    for css_file in css_files:
        if 'min.' not in css_file.name:  # Skip already minified files
            print(f"Minifying CSS: {css_file}")
            try:
                with open(css_file, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                minified_content = minify_css(original_content)
                
                # Write minified version
                minified_file = css_file.parent / f"{css_file.stem}.min{css_file.suffix}"
                with open(minified_file, 'w', encoding='utf-8') as f:
                    f.write(minified_content)
                
                print(f"  -> Created: {minified_file}")
                print(f"  -> Size reduction: {len(original_content)} -> {len(minified_content)} bytes "
                      f"({(1 - len(minified_content)/len(original_content))*100:.1f}%)")
            except Exception as e:
                print(f"  -> Error: {e}")
    
    # Process JS files
    js_files = list(static_dir.rglob('*.js'))
    for js_file in js_files:
        if 'min.' not in js_file.name:  # Skip already minified files
            print(f"Minifying JS: {js_file}")
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                minified_content = minify_js(original_content)
                
                # Write minified version
                minified_file = js_file.parent / f"{js_file.stem}.min{js_file.suffix}"
                with open(minified_file, 'w', encoding='utf-8') as f:
                    f.write(minified_content)
                
                print(f"  -> Created: {minified_file}")
                print(f"  -> Size reduction: {len(original_content)} -> {len(minified_content)} bytes "
                      f"({(1 - len(minified_content)/len(original_content))*100:.1f}%)")
            except Exception as e:
                print(f"  -> Error: {e}")


if __name__ == '__main__':
    print("Starting static file minification...")
    process_static_files()
    print("Static file minification completed!")