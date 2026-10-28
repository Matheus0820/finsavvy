import os
import pytest
from playwright.sync_api import sync_playwright

def test_temas_contraste():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content("""
            <!DOCTYPE html>
            <html lang="pt-br" data-bs-theme="light">
            <head>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body class="bg-body text-body">
                <div class="card p-3 bg-body-tertiary">
                    <h2 class="text-body">Veículos</h2>
                    <table class="table">
                        <tbody>
                            <tr><td class="text-body">Chevrolet Onix</td></tr>
                        </tbody>
                    </table>
                </div>
            </body>
            </html>
        """)
        card = page.locator(".card")
        bg_color_light = card.evaluate("node => window.getComputedStyle(node).backgroundColor")
        text_color_light = card.evaluate("node => window.getComputedStyle(node).color")
        assert bg_color_light != text_color_light

        page.evaluate("document.documentElement.setAttribute('data-bs-theme', 'dark')")
        bg_color_dark = card.evaluate("node => window.getComputedStyle(node).backgroundColor")
        text_color_dark = card.evaluate("node => window.getComputedStyle(node).color")
        assert bg_color_dark != text_color_dark
        browser.close()
