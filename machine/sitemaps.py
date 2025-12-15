from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Machine, MachineCategory


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages"""
    priority = 0.8
    changefreq = 'monthly'

    def items(self):
        return [
            'index',
            'machines',
            'categories',
            'about',
            'contact',
            'careers',
            'partners',
            'privacy_policy',
            'terms_of_service',
        ]

    def location(self, item):
        return reverse(item)


class MachineSitemap(Sitemap):
    """Sitemap for Machines"""
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return Machine.objects.filter(is_available=True)

    def location(self, obj):
        return reverse('machine_detail', args=[obj.slug])


class CategorySitemap(Sitemap):
    """Sitemap for Categories"""
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return MachineCategory.objects.all()

    def location(self, obj):
        return reverse('category_detail', args=[obj.slug])
