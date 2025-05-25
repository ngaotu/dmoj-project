from django.shortcuts import render
from judge.utils.views import DiggPaginatorMixin, QueryStringSortMixin, TitleMixin, add_file_response, generic_message, SingleObjectFormView
from django.views.generic import DetailView, FormView, ListView, TemplateView, View


class WelcomePage(TemplateView):
    template_name = "welcome_page.html"
