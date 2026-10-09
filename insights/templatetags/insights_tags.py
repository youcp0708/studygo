import json
import re

from django import template
from django.http import QueryDict
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe

from insights.permissions import get_scope

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


@register.simple_tag
def can_view_insights(user):
    """
    navbar 的 Insights 按鈕是否顯示。與 /insights/ 的存取權限使用同一個判斷（permissions.get_scope），
    確保看得到按鈕的人一定進得去、進不去的人（學生、未登入者）一定看不到。
    """
    return get_scope(user) is not None


# 回答中的「19.4%（n=67）」「19.4%」「+7.8 個百分點」：單次比對，避免同一個數字被包兩層
_NUMBER_CHIP_RE = re.compile(
    r'(?P<rate>\d+(?:\.\d+)?)\s*[%％](?:\s*[（(]\s*n\s*[=＝]\s*(?P<n>\d+)\s*[）)])?'
    r'|(?P<pp>[+＋−-]?\s*\d+(?:\.\d+)?)\s*個百分點'
)


def _number_chip(match):
    if match.group('pp'):
        return f'<span class="ins-num ins-num-pp">{match.group("pp")} 個百分點</span>'
    if match.group('n'):
        return f'<span class="ins-num">{match.group("rate")}%<small>n={match.group("n")}</small></span>'
    return f'<span class="ins-num">{match.group("rate")}%</span>'


@register.filter
def highlight_numbers(text):
    """
    AI 資料助理回答的排版：先跳脫 HTML（回答來自 LLM，視為不可信），
    再把比率、百分點標成醒目標籤，最後把換行轉成 <br>。
    """
    html = _NUMBER_CHIP_RE.sub(_number_chip, escape(text or ''))
    return mark_safe(html.replace('\n', '<br>'))


