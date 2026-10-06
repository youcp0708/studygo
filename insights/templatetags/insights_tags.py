import json

from django import template
from django.http import QueryDict
from django.utils.html import format_html

register = template.Library()


@register.filter
def rate(value):
    """把 metrics.make_rate() 的結果顯示成「13.6%（n=214）」；樣本不足時顯示「樣本不足（n=7）」。"""
    if not value:
        return '—'
    if value['suppressed']:
        return format_html('<span class="ins-muted">樣本不足（n={}）</span>', value['n'])
    return format_html('{}%<span class="ins-n">（n={}）</span>', value['rate'], value['n'])


@register.simple_tag
def query_with(query_string, key, value):
    """在目前的網址參數上替換一個參數，用於分類切換連結。"""
    q = QueryDict(query_string, mutable=True)
    q[key] = value
    return q.urlencode()


@register.filter
def pretty_json(value):
    """把工具結果排版成易讀的 JSON（資料依據用）。"""
    return json.dumps(value, ensure_ascii=False, indent=2)
