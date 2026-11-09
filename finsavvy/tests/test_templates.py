from django.test import TestCase
from django.template.loader import get_template

class SidebarTemplateTest(TestCase):
    def test_custos_variaveis_submenu_href(self):
        template = get_template('_sidebar_links.html')
        context = {'prefix': 'mobile_'}
        rendered = template.render(context)
        self.assertIn('href="#mobile_custosVariaveisSubmenu"', rendered)

    def test_veiculos_submenu_href(self):
        template = get_template('_sidebar_links.html')
        context = {'prefix': 'mobile_'}
        rendered = template.render(context)
        self.assertIn('href="#mobile_veiculosSubmenu"', rendered)