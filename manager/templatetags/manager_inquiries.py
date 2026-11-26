from django import template

from inquiries.models import Inquiry

register = template.Library()


@register.simple_tag
def new_inquiry_ids():
    return Inquiry.new_ids()
