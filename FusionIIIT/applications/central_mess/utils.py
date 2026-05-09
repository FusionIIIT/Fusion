from PyPDF2 import PdfFileWriter, PdfFileReader
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from io import StringIO
from xhtml2pdf import pisa

def render_to_pdf(template_src, context_dict={}, password=None):
    from django.template.loader import get_template
    from io import BytesIO
    from xhtml2pdf import pisa
    from PyPDF2 import PdfFileWriter, PdfFileReader
    from django.http import HttpResponse

    print('rendering the pdf\n\n\n')
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    
    if not pdf.err:
        if password:
            pdf_reader = PdfFileReader(BytesIO(result.getvalue()))
            pdf_writer = PdfFileWriter()
            for page_num in range(pdf_reader.getNumPages()):
                pdf_writer.addPage(pdf_reader.getPage(page_num))
            pdf_writer.encrypt(password)
            encrypted_result = BytesIO()
            pdf_writer.write(encrypted_result)
            return HttpResponse(encrypted_result.getvalue(), content_type='application/pdf')
        
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None