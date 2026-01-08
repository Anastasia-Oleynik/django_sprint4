from django.shortcuts import render
from django.views.generic import TemplateView


class AboutView(TemplateView):
    template_name = 'pages/about.html'


class RulesView(TemplateView):
    template_name = 'pages/rules.html'


def page_not_found(request, exception):
    template = 'pages/404.html'
    return render(request, template, status=404)


def page_forbidden(request, exception):
    template = 'pages/403csrf.html'
    return render(request, template, status=403)


def page_internal_server_error(request):
    template = 'pages/500.html'
    return render(request, template, status=500)
