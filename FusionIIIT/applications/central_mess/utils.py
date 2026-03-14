from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from io import StringIO
from xhtml2pdf import pisa

def render_to_pdf(template_src, context_dict={}):
    print('rendering the pdf\n\n\n')
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    print(result.read)
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None
