from django.contrib import admin


class BaseAdmin(admin.ModelAdmin):
    """base para todas as config do admin e adiciona donfigs comuns para todos os models aqui"""

    list_per_page = 25
    ordering = ['id']
    date_hierarchy = None
    search_fields = []
    list_filter = []
    readonly_fields = ['id']

    def get_search_fields(self, request):
        """garante q search_fields seja herdado dos filhos"""
        return super().get_search_fields(request)

    def get_list_filter(self, request):
        """ggerante q list_filter seja herdado dos filhos"""
        return super().get_list_filter(request)
