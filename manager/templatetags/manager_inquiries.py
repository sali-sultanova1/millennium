from django import template

from inquiries.models import Inquiry

register = template.Library()


@register.simple_tag
def has_new_inquiries():
    return Inquiry.has_new()
